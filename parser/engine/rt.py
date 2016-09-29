#!/usr/bin/env python
# -*- #coding: utf8 -*-


import functools
import common.config
import parser.wordform
import parser.lang.common
import parser.lang.defs
import parser.matcher
import parser.build.compiler
import common.output
import common.ifmodified
from argparse import Namespace as ns
import logging
import common.argres
from common.argres import argres
from parser.engine.entries import RtMatchEntry, RtTmpEntry, RtVirtualEntry
from parser.engine.matched import MatchedSequence, SequenceMatchRes


class RtStackCounter(object):
    def __init__(self, stack=None):
        if stack is None:
            self.__init_blank()
        else:
            self.__init_from_stack(stack)

    def __init_blank(self):
        self.__stack = []

    def __init_from_stack(self, stack):
        self.__stack = stack.__stack[:]

    def __reset_under(self, l):
        if l + 1 < len(self.__stack):
            self.__stack = self.__stack[0:l + 1]

    def __incr_level(self, l):
        assert l == len(self.__stack) or l + 1 == len(self.__stack), \
            'l={0}, len={1}, stack={2}'.format(
                l, len(self.__stack), self.__stack
            )
        if l + 1 == len(self.__stack):
            self.__stack[l] += 1
        else:
            self.__stack.append(0)
        assert l + 1 == len(self.__stack)

    def handle_trs(self, trs):
        levelpath = trs.get_levelpath()
        self.__reset_under(min(levelpath))
        for m in levelpath:
            self.__incr_level(m)

    def get_stack(self):
        return self.__stack


class MatcherContext(object):
    fcns_map = [
        ('ctx_create_fcn', 'ctx_create_fcn', lambda x: None),
        ('sequence_forked_fcn', 'sequence_forked_fcn', lambda x: None),
        ('sequence_forking_fcn', 'sequence_forking_fcn', lambda x: None),
        ('sequence_matched_fcn', 'sequence_matched_fcn', lambda x: None),
        ('sequence_failed_fcn', 'sequence_failed_fcn', lambda x: None),
        ('sequence_res_fcn', 'sequence_res_fcn', lambda x: None),
        ('ctx_complete_fcn', 'ctx_complete_fcn', lambda x: None),
    ]

    def __init__(self, owner, spec_name, **kwargs):
        self.owner = owner
        self.spec_name = spec_name
        self.__create_fcns(kwargs)
        self.sequences = []
        self.ctxs = []
        self.__new_ctxs = []
        self.__blank = True
        self.ctx_create()

    def __create_fcns(self, fcns):
        self.__fcns = {
            target: fcns[source] if source in fcns else default_fcn for source, target, default_fcn in MatcherContext.fcns_map
        }

    def set_sequences(self, sequences):
        self.sequences = sequences

    def get_sequences(self):
        return self.sequences

    def add_sequence(self, sq):
        self.sequences.append(sq)
        self.__blank = False

    def get_ctxs(self):
        return self.ctxs

    def set_ctxs(self, ctxs):
        self.ctxs = ctxs

    def get_new_ctxs(self):
        return self.__new_ctxs

    def clear_new_ctxs(self):
        self.__new_ctxs = []

    def create_ctx(self, spec_name, **kwargs):
        # if not isinstance(self.owner, ns):
        #     print list(self.__get_callstack())
        matcher = self.owner.find_matcher(spec_name)
        mc = MatcherContext(self, spec_name, **kwargs)
        self.ctxs.append((matcher, mc))
        self.__new_ctxs.append((matcher, mc))

    def called_more_than(self, ctx_name, max_count):
        cnt = 0
        for name in self.__get_callstack():
            if ctx_name != name:
                continue
            cnt += 1
            if cnt > max_count:
                return True
        return False

    def __get_callstack(self):
        o = self.owner
        while not isinstance(o, ns):
            yield o.get_name()
            o = o.owner

    def find_matcher(self, name):
        return self.owner.find_matcher(name)

    def is_blank(self):
        return self.__blank

    def sequence_forked(self, sq, new_sq):
        self.__fcns['sequence_forked_fcn']((self, sq, new_sq))

    def sequence_forking(self, sq):
        self.__fcns['sequence_forking_fcn']((self, sq))

    def sequence_matched(self, sq):
        self.__fcns['sequence_matched_fcn']((self, sq))

    def sequence_failed(self, sq):
        self.__fcns['sequence_failed_fcn']((self, sq))

    def sequence_res(self, res):
        self.__fcns['sequence_res_fcn']((self, res))

    def ctx_create(self):
        self.__fcns['ctx_create_fcn']((self, ))

    def ctx_complete(self):
        self.__fcns['ctx_complete_fcn']((self, ))

    def get_name(self):
        return self.spec_name


class RtMatchSequence(object):
    def __new__(cls, *args, **kwargs):
        obj = super(RtMatchSequence, cls).__new__(cls)
        if common.argres.logs_enabled:
            obj.logger = RtMatchSequence.__create_logger(str(obj), hex(id(obj)) + '.log')
        else:
            obj.logger = None
        return obj

    @staticmethod
    def __create_logger(logger_name, log_file, level=logging.INFO):
        log_file = common.output.output.get_output_file('hist', log_file)
        l = logging.getLogger(logger_name)
        formatter = logging.Formatter('%(asctime)s : %(message)s')
        fileHandler = logging.FileHandler(log_file, mode='w')
        fileHandler.setFormatter(formatter)

        l.setLevel(level)
        l.addHandler(fileHandler)
        return l

    def get_logger(self):
        return self.logger

    @argres(show_result=False)
    def __init__(self, based_on, indexes=None):
        if isinstance(based_on, RtMatchSequence):
            self.__init_from_sq(based_on, indexes)
        elif isinstance(based_on, ns):
            self.__init_new(based_on.matcher, based_on.initial_entry, based_on.ctx)
        else:
            raise ValueError('unsupported source for RtMatchSequence contruction {0}'.format(type(based_on)))

    @argres(show_result=False)
    def __init_new(self, matcher, initial_entry, ctx):
        self.__matcher = matcher
        self.__ctx = ctx
        self.__entries = []
        self.__all_entries = []
        self.__anchors = []
        self.__links = {}
        self.__forms_csum = set()
        self.__links_csum = set()

        self.__stack = RtStackCounter()
        self.__append_entries(initial_entry)

    @argres(show_result=True)
    def __init_from_sq(self, sq, indexes=None):
        self.__matcher = sq.__matcher
        self.__ctx = sq.__ctx
        self.__entries = []
        self.__all_entries = []
        self.__anchors = []
        self.__forms_csum = set()
        self.__confirmed_csum = set()

        sq.__ctx.sequence_forking(sq)

        self.__stack = RtStackCounter(stack=sq.__stack)

        if indexes is not None:
            assert isinstance(indexes, tuple) and len(indexes) == 2
            assert indexes[0] == 0
            l = indexes[0]
            r = indexes[1]
            if r < 0:
                r += len(sq.__all_entries) + 1
            indexes = list(range(l, r))

        self.__copy_all_entries(sq, indexes=indexes)
        self.__copy_links(sq, indexes=indexes)
        # self.__copy_anchors(sq, indexes=indexes)

        sq.__ctx.sequence_forked(sq, self)

    def __copy_all_entries(self, sq, indexes):
        for i, e in filter(
            lambda idx_entry: indexes is None or idx_entry[0] in indexes,
            enumerate(sq.__all_entries)
        ):
            self.__append_entries(
                RtMatchEntry(self, e) if isinstance(e, RtMatchEntry) else RtVirtualEntry(self, e)
            )
        for e in self.__all_entries:
            e.resolve_matched_rtmes()
        if indexes is None:
            assert len(self.__all_entries) == len(sq.__all_entries) and len(self.__entries) == len(sq.__entries)

    def __copy_links(self, sq, indexes):
        self.__links = {}
        for master, slaves in list(sq.__links.items()):
            master_offset = master.get_offset()
            if indexes is not None and master_offset not in indexes:
                continue
            my_master = self[master_offset]
            self.__links[my_master] = {}
            for slave, details in list(slaves.items()):
                slave_offset = slave.get_offset()
                if indexes is not None and slave_offset not in indexes:
                    continue
                my_slave = self[slave_offset]
                self.__links[my_master][my_slave] = details[:]

    def __copy_anchors(self, sq, indexes):
        self.__anchors = []
        for anchor in sq.__anchors:
            a_offset = anchor.get_offset()
            if indexes is not None and a_offset not in indexes:
                continue
            self.__anchors.append(self[a_offset])

    @argres()
    def subseq(self, start, stop):
        return RtMatchSequence(self, indexes=(start, stop))

    def get_anchors(self):
        return self.__anchors

    def __add_anchor(self, rtme):
        self.__anchors.append(rtme)

    @argres()
    def handle_forms(self, forms):
        new_sq = []
        again = [self, ]
        while again:
            sq = again.pop(0)
            r = sq.__handle_forms(forms)
            new_sq.extend(r.results)
            again.extend(r.again)
        return new_sq

    def __handle_forms(self, forms):
        head = self.__all_entries[-1]
        if isinstance(head, RtTmpEntry):
            return ns(
                results=[
                    ns(
                        sq=self,
                        valid=True if head.get_subctx() is not None else False,
                        fini=False
                    ), ],
                again=[]
            )

        hres = ns(
            results=[],
            again=[]
        )

        trs = head.find_transitions(forms)
        if not trs:
            return hres

        trs_sqs = [self, ] + list(map(lambda x: RtMatchSequence(self), trs[0:-1]))
        for sq, (form, t) in zip(trs_sqs, trs):
            res = sq.__handle_trs(t, form)
            for r in res:
                if r.valid:
                    if not r.again:
                        hres.results.append(r)
                    else:
                        hres.again.append(r.sq)
                else:
                    self.__ctx.sequence_failed(r.sq)
                if r.fini:
                    self.__ctx.sequence_res(r)

        return hres

    @argres()
    def __handle_trs(self, trs, form):
        to = trs.get_to()
        if to.fixed():
            return self.__handle_fixed_trs(trs, form)
        else:
            return self.__handle_dynamic_trs(trs, form)

    @argres()
    def append(self, rtme):
        self.__append_entries(rtme)

        if isinstance(rtme, RtTmpEntry):
            return True

        if isinstance(rtme, RtVirtualEntry) and not rtme.closed():
            return True

        res = self.__test_rtme_rules(rtme)
        if not res.valid:
            return False

        self.__update_affected_links(res.affected_links)

        return True

    @argres()
    def __test_rtme_rules(self, rtme):
        affected_links = []
        rtme_pares = self.__find_affected_pares(rtme, find_all=True)
        while rtme_pares:
            e, ee = rtme_pares.pop(0)
            res = e.handle_rules(on_entry=ee)
            if res.later:
                continue
            if res.again:
                rtme_pares.extend(self.__find_affected_pares(e, find_all=True))
            elif not res.valid:
                return ns(valid=False, affected_links=[])
            if ee.closed() and ee.modified():
                rtme_pares.extend(self.__find_affected_pares(ee))

            affected_links.extend(res.affected_links)

        return ns(valid=True, affected_links=affected_links)

    def __update_affected_links(self, links):
        for l in links:
            l.rule.apply_on(l.rtme, l.other_rtme, [l.created_by, ])

    @argres()
    def __find_affected_pares(self, rtme, find_all=False):
        if find_all:
            return list(map(
                lambda other_rtme: (rtme, other_rtme),
                self.get_entries(hidden=True, exclude=rtme)
            )) + list(map(
                lambda other_rtme: (other_rtme, rtme),
                self.get_entries(hidden=True, exclude=rtme)
            ))
        return list(map(
            lambda other_rtme: (rtme, other_rtme),
            self.get_entries(hidden=True, exclude=rtme)
        ))

    @argres()
    def __handle_fixed_trs(self, trs, form):
        to = trs.get_to()
        self.__stack.handle_trs(trs)

        if to.is_virtual():
            rtme = RtVirtualEntry(self, ns(form=form,
                                           spec_state_def=to,
                                           rtms_offset=len(self.__all_entries)
                                           )
                                  )
        else:
            rtme = RtMatchEntry(self, ns(form=form,
                                         spec_state_def=to,
                                         rtms_offset=len(self.__all_entries)
                                         )
                                )

        if not self.append(rtme):
            return [ns(sq=self, valid=False, fini=False, again=False), ]

        if to.is_fini():
            return [ns(sq=self, valid=self.__on_fini(), fini=True, again=False), ]
        return [ns(sq=self, valid=True, fini=False, again=to.is_virtual()), ]

    @argres()
    def __handle_dynamic_trs(self, trs, form):
        head = self.__all_entries[-1]
        if isinstance(head, RtTmpEntry):
            return [ns(sq=self, valid=True, fini=False, again=False), ]

        to = trs.get_to()

        if self.__dynamic_ctx_overflow(to.get_include_name()):
            return [ns(sq=self, valid=False, fini=False, again=False), ]

        self.__stack.handle_trs(trs)

        # Create virtual entry, awaiting for subsequence
        rte = RtTmpEntry(
            self,
            ns(
                form=form,
                spec_state_def=to,
                rtms_offset=len(self.__all_entries)
            )
        )

        self.__append_entries(rte)
        self.__ctx.create_ctx(
            to.get_include_name(),
            ctx_create_fcn=lambda sub_ctx2: self.__subctx_create(sub_ctx2[0], rte),
            sequence_res_fcn=lambda sub_ctx_res: self.__submatcher_res(sub_ctx_res[0], rte, sub_ctx_res[1]),
            sequence_forked_fcn=lambda sub_ctx_sq_new_sq: self.__submatcher_forked(sub_ctx_sq_new_sq[0], sub_ctx_sq_new_sq[1], sub_ctx_sq_new_sq[2], rte),
            ctx_complete_fcn=lambda sub_ctx3: self.__subctx_complete(sub_ctx3[0], rte)
        )
        return [ns(sq=self, valid=True, fini=False, again=False), ]

    def __dynamic_ctx_overflow(self, next_ctx_name):
        return self.__ctx.called_more_than(next_ctx_name, 0)

    def __subctx_create(self, sub_ctx, rte):
        # print '__submatcher_create', sub_ctx, rte
        rte.set_subctx(sub_ctx)

    def __submatcher_res(self, sub_ctx, rte, res):
        # print '__submatcher_res', res
        rte.add_sequence_res(sub_ctx, res)

    def __submatcher_forked(self, sub_ctx, sq, new_sq, rte):
        # print '__submatcher_forked'
        rte.add_forked_sequence(sub_ctx, new_sq)

    def __subctx_complete(self, sub_ctx, rte):
        # print '__submatcher_complete', sub_ctx, rte
        rte.unset_subctx(sub_ctx)

    def __subctx_failed(self, sub_ctx, rte):
        # print '__submatcher_failed', sub_ctx, rte
        rte.unset_subctx(sub_ctx)

    @argres()
    def __on_fini(self):
        for e in self.get_entries(hidden=False):
            if e.has_pending(required_only=True):
                return False
        return True

    def __append_entries(self, rtme):
        self.__all_entries.append(rtme)
        if rtme.get_spec().add_to_seq():
            self.__entries.append(rtme)
        self.__forms_csum.add(rtme.get_form().get_uniq())
        if rtme.get_spec().is_anchor():
            self.__add_anchor(rtme)

    def __getitem__(self, index):
        return self.__all_entries[index]

    def get_rule_name(self):
        return self.__matcher.get_name()

    def print_sequence(self):
        res = '{0} <'.format(self.get_rule_name())
        for e in self.__entries:
            f = e.get_form()
            res += '{0} '.format(f.get_word())
        res += '>'
        return res

    def get_links(self):
        return self.__links

    @argres(show_result=False)
    def add_link(self, links):
        assert isinstance(links, list)
        for l in links:
            assert isinstance(l, ns)
            self.__mk_link(l)

    @argres(show_result=False)
    def __mk_link(self, l):
        if l.master not in self.__links:
            self.__links[l.master] = {}
            self.__links[l.master][l.slave] = []
        elif l.slave not in self.__links[l.master]:
            self.__links[l.master][l.slave] = []
        links = self.__links[l.master][l.slave]
        if not l.rewrite_existing:
            links.append(
                {
                    'revisions': {
                        'master': l.master.get_form().revision(),
                        'slave': l.slave.get_form().revision(),
                        'track': l.track_revisions,
                        'created-by': l.created_by,
                        'rule': l.rule,
                    },
                    'qualifiers': l.qualifiers,
                    'details': l.debug,
                }
            )
        else:
            offset = self.__link_exists(links, l)
            if offset is None:
                links.append(
                    {
                        'revisions': {
                            'master': l.master.get_form().revision(),
                            'slave': l.slave.get_form().revision(),
                            'track': l.track_revisions,
                            'created-by': l.created_by,
                            'rule': l.rule,
                        },
                        'qualifiers': l.qualifiers,
                        'details': l.debug,
                    }
                )
            else:
                links[offset] = {
                    'revisions': {
                        'master': l.master.get_form().revision(),
                        'slave': l.slave.get_form().revision(),
                        'track': l.track_revisions,
                        'created-by': l.created_by,
                        'rule': l.rule,
                    },
                    'qualifiers': l.qualifiers,
                    'details': l.debug,
                }

    def __link_exists(self, links, l):
        for i, ll in enumerate(links):
            if ll['revisions']['created-by'] == l.created_by:
                return i
        return None

    def get_trackable_links(self, rtme):
        trackable = []
        for master, slaves in list(self.__links.items()):
            for slave, links in list(slaves.items()):
                if slave is not rtme:
                    continue
                for link in links:
                    if not link['revisions']['track']:
                        continue
                    trackable.append(
                        ns(
                            rtme=rtme,
                            other_rtme=master,
                            created_by=link['revisions']['created-by'],
                            rule=link['revisions']['rule']
                        )
                    )
        return trackable

    def get_stack(self):
        return self.__stack.get_stack()

    def has_item(self, name=None, starts_with=None, cmp_fcn=None):
        assert name is not None or starts_with is not None or cmp_fcn is not None
        assert name is None and cmp_fcn is None
        for e in self.__entries:
            name = str(e.get_name())
            if name.startswith(starts_with):
                return True
        return False

    def get_entries(self, hidden=False, exclude=None):
        src = self.__entries if not hidden else self.__all_entries
        if exclude is None:
            return src[:]
        return [e for e in src if e is not exclude]

    def get_ctx(self):
        return self.__ctx

    def __repr__(self):
        return "RtMatchSequence(objid={0})".format(hex(id(self)))

    def __str__(self):
        return "RtMatchSequence(objid={0})".format(hex(id(self)))

    def __eq__(self, other):
        assert isinstance(other, RtMatchSequence)
        if id(self) == id(other):
            return True
        return all((self.__forms_csum == other.__forms_csum,
                    self.__confirmed_csum == other.__confirmed_csum))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__forms_csum, self.__confirmed_csum))


class SpecMatcher(object):
    def __init__(self, owner, compiled_spec):
        assert owner is not None
        assert isinstance(compiled_spec, parser.build.compiler.CompiledSpec)
        self.__owner = owner
        self.__compiled_spec = compiled_spec
        self.__name = self.__compiled_spec.get_name()

    def match(self, ctx, sentence):
        for forms in sentence:
            res = self.__handle_sequences(ctx, forms)
            if res.complete:
                return res
        return ns(complete=False)

    def __create_new_sequence(self, ctx):
        ini_spec = self.__compiled_spec.get_inis()[0]
        ctx.add_sequence(
            RtMatchSequence(
                ns(
                    matcher=self,
                    initial_entry=RtMatchEntry(None, ns(
                        form=parser.wordform.SpecStateIniForm(),
                        spec_state_def=ini_spec,
                        rtms_offset=0)
                    ),
                    ctx=ctx,
                )
            )
        )

    def __handle_forms_result(self, ctx, res, next_sequences):
        if not res.fini:
            next_sequences.append(res.sq)
        else:
            if self.__compiled_spec.get_validate() is None or self.__compiled_spec.get_validate().validate(res.sq):
                ms = MatchedSequence(res.sq)
                ctx.sequence_matched(ms)
            else:
                ctx.sequence_failed(res.sq)

    def __handle_sequences(self, ctx, forms):
        if ctx.is_blank():
            self.__create_new_sequence(ctx)

        if ctx.get_sequences():
            next_sequences = []
            for sq in ctx.get_sequences():
                # print "handling", sq
                for res in sq.handle_forms(forms):
                    self.__handle_forms_result(ctx, res, next_sequences)
            ctx.set_sequences(next_sequences)
            if not next_sequences:
                ctx.ctx_complete()
                return ns(complete=True)
        return ns(complete=False)

    def __print_sequences(self, ctx):
        for sq in ctx.get_sequences:
            sq.print_sequence()

    def get_name(self):
        return self.__name

    def get_compiled_spec(self):
        return self.__compiled_spec


class Matcher(object):
    def __init__(self, compiled):
        self.__compiled = compiled

    def __select_most_complete(self, ctx):
        max_entries = functools.reduce(
            lambda prev_max, msq:
                msq.get_entry_count(
                    hidden=False,
                    virtual=False
                ) if prev_max < msq.get_entry_count(
                    hidden=False,
                    virtual=False
                ) else prev_max,
            ctx.matched_sqs,
            0
        )
        ctx.matched_sqs = list(filter(lambda msq: max_entries <= msq.get_entry_count(hidden=False), ctx.matched_sqs))

    def __create_initial_ctxs(self, ctx):
        ctx.ctxs = list(map(
            lambda m: (
                m,
                parser.engine.rt.MatcherContext(
                    ctx,
                    '__root',
                    sequence_matched_fcn=lambda sq_ctx_sq: ctx.matched_sqs.add(sq_ctx_sq[1]),
                )
            ),
            self.__compiled.get_primary()
        ))

    def __create_ctx(self):
        return ns(
            matched_sqs=set(),
            find_matcher=self.__compiled.get_matcher
        )

    def __handle_ctx(self, matcher, ctx, s):
        ctx.clear_new_ctxs()

        next_subctxs = []
        for mtchr, m_ctx in ctx.get_ctxs():
            res = self.__handle_ctx(mtchr, m_ctx, s)
            if not res.complete:
                next_subctxs.append((mtchr, m_ctx))
        ctx.set_ctxs(next_subctxs)

        res = matcher.match(ctx, s)
        if res.complete:
            return res

        for mtchr, m_ctx in ctx.get_new_ctxs():
            self.__handle_ctx(mtchr, m_ctx, s)

        return ns(complete=False)

    def match_sentence(self, sentence, ctx=None, most_complete=False):
        if ctx is None:
            ctx = self.__create_ctx()
            self.__create_initial_ctxs(ctx)

        sentence += [parser.wordform.SentenceFini(), ]

        for s in sentence:
            s = [s, ]
            for matcher, m_ctx in ctx.ctxs:
                self.__handle_ctx(matcher, m_ctx, s)

        if most_complete:
            self.__select_most_complete(ctx)
        smr = SequenceMatchRes(ctx.matched_sqs)
        return smr
