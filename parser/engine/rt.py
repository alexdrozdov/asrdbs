#!/usr/bin/env python
# -*- #coding: utf8 -*-


import logging
import common.argres
import common.config
import common.output
import parser.spare.wordform
import parser.build.compiler
from common.argres import argres
from argparse import Namespace as ns
from parser.engine.entries import RtMatchEntry, RtVirtualEntry, \
    RtSiblingLeaderEntry, RtSiblingFollowerEntry, RtSiblingCloserEntry


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


class Backlog(object):
    def __init__(self, master=None):
        self.__master = master
        self.__slaves = []
        self.__entries = []
        if master is not None:
            master.attach_slave(self)

    def clone(self):
        bl = Backlog(self.__master)
        bl.__entries = [e for e in self.__entries]
        return bl

    def fetch_master(self):
        assert self.__master is not None
        assert not self.__entries
        assert len(self.__master.__slaves) == 1
        self.__entries = self.__master.__entries
        self.__master.__entries = []

    def attach_slave(self, slave):
        self.__slaves.append(slave)

    def forget_slave(self, slave):
        try:
            self.__slaves.remove(slave)
        except ValueError:
            pass

    def push_head(self, entry):
        if entry:
            if not self.__slaves:
                self.__entries.append(entry)
            else:
                for s in self.__slaves:
                    s.push_head(entry)

    def push_tail(self, entry):
        if self.__slaves:
            raise RuntimeError('Malicious pop push')
        self.__entries.insert(0, entry)

    def pop_tail(self):
        if self.__entries:
            return self.__entries.pop(0)
        raise RuntimeError('Backlog is empty')

    def get_tail(self):
        if self.__entries:
            return self.__entries[0]
        raise RuntimeError('Backlog is empty')

    def empty(self):
        if self.__entries:
            return False
        return True

    def __iter__(self):
        return iter(self.__entries)


class SupervisedSequence(object):
    def __init__(self, sq, checkedout, confirmed):
        self.sq = sq
        self.checkedout = checkedout
        self.confirmed = confirmed


class SupervisedContext(object):
    def __init__(self, ctx, matcher, checkedout):
        self.ctx = ctx
        self.matcher = matcher
        self.checkedout = checkedout


class CheckedoutCtx(object):
    def __init__(self, ctx, sequences):
        self.ctx = ctx
        self.__sequences = {id(sq): SupervisedSequence(
            sq=sq, checkedout=False, confirmed=False)
            for sq in sequences}

    def sequences(self):
        return [sq.sq for sq in self.__sequences.values()]

    def commit(self):
        for svsq in self.__sequences.values():
            assert not svsq.checkedout
            if isinstance(svsq.sq, UnfrozenSequence):
                continue
            if svsq.confirmed:
                self.ctx.add_sequence(svsq.sq)
            else:
                self.ctx.sequence_failed(svsq.sq)

    def checkout_sequence(self, sq):
        svsq = self.__sequences.get(id(sq), None)
        if svsq is not None:
            assert not svsq.checkedout
            svsq.checkedout = True
            return
        self.__sequences[id(sq)] = SupervisedSequence(sq, True, False)

    def confirm_sequence(self, sq):
        svsq = self.__sequences.get(id(sq), None)
        assert svsq is not None and svsq.checkedout
        svsq.checkedout = False
        svsq.confirmed = True

    def fail_sequence(self, sq):
        svsq = self.__sequences.pop(id(sq), None)
        assert svsq is not None and svsq.checkedout
        self.ctx.sequence_failed(sq)

    def ignore_sequence(self, sq):
        svsq = self.__sequences.get(id(sq), None)
        assert svsq is not None and svsq.checkedout
        svsq.checkedout = False
        svsq.confirmed = False

    def complete_sequence(self, sq):
        svsq = self.__sequences.pop(id(sq), None)
        assert svsq is not None and svsq.checkedout
        self.ctx.sequence_matched(sq)

    def freeze(self, frozen_sq):
        sq = frozen_sq.sq
        svsq = self.__sequences.pop(id(sq), None)
        assert svsq is not None and svsq.checkedout
        self.ctx.add_frozen(frozen_sq)

    def wait_sequence(self, sq):
        self.ctx.add_wait(sq)


class CheckedoutCtxs(object):
    def __init__(self, ctx, ctxs):
        self.ctx = ctx
        self.__ctxs = {id(c): SupervisedContext(ctx=c, matcher=m, checkedout=False)
                       for m, c in ctxs}

    def ctxs(self):
        return self.__ctxs.values()

    def commit(self):
        for svctx in self.__ctxs.values():
            assert not svctx.checkedout
            self.ctx.add_ctx(svctx.matcher, svctx.ctx)

    def checkout(self, ctx):
        svctx = self.__ctxs.get(id(ctx), None)
        assert svctx is not None
        assert not svctx.checkedout
        svctx.checkedout = True

    def confirm(self, ctx):
        svsq = self.__ctxs.get(id(ctx), None)
        assert svsq is not None and svsq.checkedout
        svsq.checkedout = False

    def complete(self, ctx):
        svsq = self.__ctxs.pop(id(ctx), None)
        assert svsq is not None and svsq.checkedout
        svsq.ctx.ctx_complete()


class MatcherContext(object):

    max_sparse_count = 1
    max_sequential_count = 0

    def __init__(self, event_listener, owner, spec_name, offset=0):
        self._event_listener = event_listener
        self.owner = owner
        self.spec_name = spec_name
        self.__offset = offset
        self.sequences = []
        self.ctxs = []
        self.__blank = True
        self.__backlog = Backlog()
        self.__frozen = []
        self.__awaiting = []
        self.ctx_create()

    def empty(self):
        return len(self.sequences) == 0 and len(self.__awaiting) == 0

    def get_head(self):
        assert len(self.sequences) == 1
        head = self.sequences[0].get_head()
        return ns(
            form=head.get_form()
        )

    def get_heads(self):
        return [ns(form=sq.get_head().get_form()) for sq in self.sequences]

    def split_by_sequences(self):
        res = []
        print('split sequences sequences', self.sequences)
        for sq in self.sequences:
            m = MatcherContext(
                ContextEventsForwarder(self._event_listener),
                self.owner,
                self.spec_name,
                self.__offset
            )
            m.sequences = [sq, ]
            res.append(m)
        return res

    def get_sequences(self):
        return self.sequences

    def add_sequence(self, sq):
        self.sequences.append(sq)
        self.__blank = False

    def add_ctx(self, matcher, ctx):
        self.ctxs.append((matcher, ctx))

    def create_ctx(self, spec_name, event_listener=None, offset=0):
        matcher = self.owner.find_matcher(spec_name)
        mc = MatcherContext(event_listener, self, spec_name)
        self.ctxs.append((matcher, mc))
        return mc

    def checkout_sequences(self):
        sequences = self.sequences
        self.sequences = []
        return CheckedoutCtx(self, sequences)

    def checkout_contexts(self):
        ctxs = self.ctxs
        self.ctxs = []
        return CheckedoutCtxs(self, ctxs)

    def recursed_at_offset(self, ctx_name, offset):
        sparse_calls = 0
        sequential_calls = 0
        for se in self.__get_callstack():
            if se.offset < offset:
                return False
            if ctx_name == se.name:
                sparse_calls += 1
                sequential_calls += 1
                if sparse_calls > MatcherContext.max_sparse_count:
                    return True
                if sequential_calls > MatcherContext.max_sequential_count:
                    return True
                continue

            sequential_calls = 0

        return False

    def __get_callstack(self):
        o = self.owner
        while not isinstance(o, MatcherCallbacks):
            yield ns(
                name=o.get_name(),
                offset=o.get_offset()
            )
            o = o.owner

    def find_matcher(self, name):
        return self.owner.find_matcher(name)

    def add_wait(self, awaiting_sq):
        self.__awaiting.append(awaiting_sq)

    def del_wait(self, awaiting_sq):
        self.__awaiting.remove(awaiting_sq)

    def add_frozen(self, frozen_sq):
        self.__frozen.append(frozen_sq)

    def unfreeze_one(self):
        frozen = self.__frozen.pop()
        sq = frozen.pop_sequence()
        self.add_sequence(sq)
        if frozen:
            self.__frozen.append(frozen)

    def push_forms(self, forms):
        self.__backlog.push_head(forms)
        for _, ctx in self.ctxs:
            ctx.push_forms(forms)

    def push_sentence(self, sentence):
        for forms in sentence:
            self.push_forms(forms)

    def has_backlog(self):
        if self.__blank:
            return not self.__backlog.empty()
        for sq in self.sequences:
            if sq.has_backlog():
                return True
        return False

    def backlog(self):
        return self.__backlog

    def get_slave_backlog(self):
        return Backlog(self.__backlog)

    def has_frozen(self):
        return len(self.__frozen) > 0

    def is_blank(self):
        return self.__blank

    def get_name(self):
        return self.spec_name

    def get_offset(self):
        return self.__offset

    def sequence_forked(self, sq, new_sq):
        self._event_listener.sequence_forked(self, sq, new_sq)

    def sequence_forking(self, sq):
        self._event_listener.sequence_forking(self, sq)

    def sequence_matched(self, sq):
        self.__backlog.forget_slave(sq.backlog())
        self._event_listener.sequence_matched(self, sq)

    def sequence_failed(self, sq):
        self.__backlog.forget_slave(sq.backlog())
        self._event_listener.sequence_failed(self, sq)

    def sequence_res(self, res):
        self._event_listener.sequence_res(self, res)

    def ctx_create(self):
        self._event_listener.ctx_create(self)

    def ctx_complete(self):
        self._event_listener.ctx_complete(self)


class UnfrozenSequence(object):
    def __init__(self, sq, trs):
        self.__sq = sq
        self.__trs = trs

    def has_backlog(self):
        return True

    def fetch_transitions(self):
        return NextSequenceStep(
            sq=self.__sq,
            valid=True,
            awaiting=False,
            frozen=False,
            transitions=[self.__trs, ]
        )


class RtMatchSequence(object):

    dynamic_trs_fine = 0.4

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

        self.__backlog = ctx.get_slave_backlog()
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

        self.__backlog = sq.__backlog.clone()
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
            self.__append_entries(e.copy_for_owner(self))
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

    def clone(self):
        return RtMatchSequence(self)

    @argres()
    def subseq(self, start, stop):
        return RtMatchSequence(self, indexes=(start, stop))

    def backlog(self):
        return self.__backlog

    def has_backlog(self):
        return not self.__backlog.empty()

    def __add_anchor(self, rtme):
        self.__anchors.append(rtme)

    def fetch_transitions(self):
        if self.__backlog.empty():
            return NextSequenceStep(
                sq=self,
                valid=True,
                awaiting=False,
                frozen=False,
                transitions=[]
            )

        head = self.__all_entries[-1]
        forms = self.__backlog.pop_tail()
        transitions = list(self.find_transitions(head, forms))
        return NextSequenceStep(
            sq=self,
            valid=len(transitions) > 0,
            awaiting=False,
            frozen=False,
            transitions=transitions
        )

    def find_transitions(self, head, forms):
        trs = head.find_transitions(forms)
        for form, t in trs:
            to = t.get_to()
            if to.fixed() or form.get_position() is None:
                yield NextSequenceStepTransition(
                    form=form,
                    trs_def=t,
                    fixed=True,
                    probability=1.0
                )
            elif not self.__dynamic_ctx_overflow(
                to.get_include_name(),
                offset=form.get_position(),
            ):
                yield NextSequenceStepTransition(
                    form=form,
                    trs_def=t,
                    fixed=False,
                    probability=RtMatchSequence.dynamic_trs_fine
                )

    def follow(self, trs):
        res = self.__handle_trs(trs.trs_def, trs.form)
        if res.again:
            self.__backlog.push_tail([trs.form, ])
        return res

    @argres()
    def __handle_trs(self, trs, form):
        to = trs.get_to()
        if to.fixed():
            return self.__handle_fixed_trs(trs, form)
        else:
            return self.__handle_dynamic_trs(trs, form)

    def reapplay(self, sq, spec):
        res = self.__reapply_entries(sq, spec)
        if not res.valid:
            return False
        self.__reapply_links(sq, res.remap)
        return True

    def __reapply_entries(self, sq, spec):
        remap = {}
        for rtme in sq.__entries:
            self.__pop_backlog_form(rtme.get_form())
            if rtme.get_spec().is_anchor():
                n_rtme = parser.engine.entries.ForeignAnchorEntry(
                    self,
                    ns(
                        rtme=rtme,
                        spec_state_def=spec,
                        rtms_offset=len(self.__all_entries)
                    )
                )
                if not spec.is_static_applicable(n_rtme.get_form()):
                    return ns(valid=False, remap={})
                if not self.append(n_rtme):
                    return ns(valid=False, reamp={})
                remap[rtme] = n_rtme
            else:
                n_rtme = parser.engine.entries.ForeignEntry(
                    self,
                    ns(
                        rtme=rtme,
                        rtms_offset=len(self.__all_entries)
                    )
                )
                self.__append_entries(n_rtme)
                remap[rtme] = n_rtme
        return ns(valid=True, remap=remap)

    def __reapply_links(self, sq, remap):
        for master, slaves in list(sq.__links.items()):
            my_master = remap[master]
            self.__links[my_master] = {}
            for slave, details in list(slaves.items()):
                my_slave = remap[slave]
                self.__links[my_master][my_slave] = details[:]

    def __pop_backlog_form(self, form):
        f = set((i.get_uniq() for i in self.__backlog.get_tail()))
        if form.get_uniq() in f:
            self.__backlog.pop_tail()

    @argres()
    def append(self, rtme):
        self.__append_entries(rtme)

        if not rtme.closed():
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

    def __entry_from_spec(self, spec, form):
        if spec.is_sibling_leader():
            cls_name = RtSiblingLeaderEntry
        elif spec.is_sibling_follower():
            cls_name = RtSiblingFollowerEntry
        elif spec.is_sibling_closer():
            cls_name = RtSiblingCloserEntry
        elif spec.is_virtual():
            cls_name = RtVirtualEntry
        else:
            cls_name = RtMatchEntry

        form = form.copy({'ro', 'w_once', 'morf'})
        return cls_name(
            self,
            ns(
                form=form,
                spec_state_def=spec,
                rtms_offset=len(self.__all_entries)
            )
        )

    @argres()
    def __handle_fixed_trs(self, trs, form):
        to = trs.get_to()
        self.__stack.handle_trs(trs)

        rtme = self.__entry_from_spec(to, form)

        if not self.append(rtme):
            return TrsResult(sq=self, valid=False, fini=False, again=False, wait=False)

        if to.is_fini():
            return TrsResult(sq=self, valid=self.__on_fini(), fini=True, again=False, wait=False)
        return TrsResult(sq=self, valid=True, fini=False, again=to.is_virtual(), wait=False)

    @argres()
    def __handle_dynamic_trs(self, trs, form):
        to = trs.get_to()
        sq = AwaitingSequence(self, to)
        el = AwaitingEventListener(sq)

        dependent_ctx = self.__ctx.create_ctx(
            to.get_include_name(),
            event_listener=el,
            offset=form.get_position(),
        )
        dependent_ctx.push_forms([form, ])
        for f in self.__backlog:
            dependent_ctx.push_forms(f)

        return TrsResult(sq=sq, valid=True, fini=False, again=False, wait=True)

    def __dynamic_ctx_overflow(self, next_ctx_name, offset):
        return self.__ctx.recursed_at_offset(next_ctx_name, offset)

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

    def get_head(self):
        return self.__all_entries[-1]

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

    def __iter__(self):
        return iter(self.__all_entries)

    def reversed(self):
        l = len(self.__all_entries)
        for i in range(l - 1, -1, -1):
            yield self.__all_entries[i]


class TrsResult(object):

    __slots__ = ('sq', 'valid', 'fini', 'again', 'wait')

    def __init__(self, sq, valid, fini, again, wait):
        self.sq = sq
        self.valid = valid
        self.fini = fini
        self.again = again
        self.wait = wait


class SequenceCloner(object):
    def __init__(self, c_out_ctx, obj):
        self.__c_out = c_out_ctx
        self.__obj = obj
        self.__obj_used = False

    def get(self):
        obj = self.__obj
        if self.__obj_used:
            obj = obj.clone()
        self.__obj_used = True
        self.__c_out.checkout_sequence(obj)
        return obj


class AggregatedCtxTransitions(list):
    def __init__(self):
        super().__init__()
        self.__probabilities = []

    def append(self, v):
        super().append(v)
        self.__probabilities.extend([t.probability for t in v.transitions])

    def probabilities(self):
        return sorted(self.__probabilities)


class TransitionAttempt(object):

    __slots__ = ('sq', 'trs')

    def __init__(self, sq, trs):
        self.sq = sq
        self.trs = trs


class NextSequenceStep(object):

    __slots__ = ('sq', 'valid', 'awaiting', 'frozen', 'transitions')

    def __init__(self, sq, valid, awaiting, frozen, transitions):
        self.sq = sq
        self.valid = valid
        self.awaiting = awaiting
        self.frozen = frozen
        self.transitions = transitions


class NextSequenceStepTransition(object):

    __slots__ = ('form', 'trs_def', 'fixed', 'probability')

    def __init__(self, form, trs_def, fixed, probability):
        self.form = form
        self.trs_def = trs_def
        self.fixed = fixed
        self.probability = probability


class FrozenSequence(list):
    def __init__(self, sq):
        super().__init__()
        self.sq = sq

    def pop_sequence(self):
        trs = self.pop()
        sq = self.sq
        if self:
            sq = sq.clone()
        return UnfrozenSequence(sq, trs)


class AwaitingSequence(object):
    def __init__(self, sq, spec):
        super().__init__()
        self.__sq = sq
        self.__to_spec = spec

    def __pop_sequence(self):
        return AwaitedSequence(self.__sq.clone(), self.__to_spec)

    def submatcher_matched(self, subsq):
        sq = self.__pop_sequence()
        if sq.reapplay(subsq):
            ctx = self.__sq.get_ctx()
            ctx.add_sequence(sq)

    def subctx_complete(self, sub_ctx):
        ctx = self.__sq.get_ctx()
        ctx.del_wait(self)


class AwaitedSequence(object):
    def __init__(self, sq, spec):
        super().__init__()
        self.__sq = sq
        self.__to_spec = spec

    def has_backlog(self):
        return self.__sq.has_backlog()

    def backlog(self):
        return self.__sq.backlog()

    def fetch_transitions(self):
        if not self.has_backlog():
            return NextSequenceStep(
                sq=self,
                valid=True,
                awaiting=False,
                frozen=False,
                transitions=[]
            )

        sq = self.__sq
        last_form = sq[-1]
        head = parser.engine.entries.StandaloneEntry(self.__to_spec, last_form)
        forms = sq.backlog().pop_tail()
        transitions = list(sq.find_transitions(head, forms))
        return NextSequenceStep(
            sq=self.__sq,
            valid=len(transitions) > 0,
            awaiting=False,
            frozen=False,
            transitions=transitions
        )

    def reapplay(self, subseq):
        return self.__sq.reapplay(subseq, self.__to_spec)


class SpecMatcher(object):
    def __init__(self, owner, compiled_spec):
        assert owner is not None
        assert isinstance(compiled_spec, parser.build.compiler.CompiledSpec)
        self.__owner = owner
        self.__compiled_spec = compiled_spec
        self.__name = self.__compiled_spec.get_name()

    def is_applicable(self, form):
        return self.__compiled_spec.is_applicable(form)

    def match(self, ctx):
        self.__handle_sequences(ctx)
        return ns(complete=ctx.empty())

    def once(self, ctx):
        self.__handle_sequences(ctx)

    def __create_new_sequence(self, ctx):
        ini_spec = self.__compiled_spec.get_inis()[0]
        sq = RtMatchSequence(
            ns(
                matcher=self,
                initial_entry=RtMatchEntry(None, ns(
                    form=parser.spare.wordform.SpecStateIniForm(),
                    spec_state_def=ini_spec,
                    rtms_offset=0)
                ),
                ctx=ctx,
            )
        )
        sq.backlog().fetch_master()
        ctx.add_sequence(sq)

    def __handle_sequences(self, ctx):
        if ctx.is_blank():
            self.__create_new_sequence(ctx)

        while ctx.has_backlog():
            c_out = ctx.checkout_sequences()
            to_execute = self.__find_executables(c_out)
            self.__execute_sequences(c_out, to_execute)

            c_out.commit()

            if not ctx.has_backlog() and ctx.has_frozen():
                ctx.unfreeze_one()

        return ns(complete=ctx.empty())

    def __execute_sequences(self, c_out, to_execute):
        for ta in to_execute:
            res = ta.sq.follow(ta.trs)

            if not res.valid:
                c_out.fail_sequence(ta.sq)
                continue

            if res.fini:
                c_out.complete_sequence(ta.sq)
                continue

            if res.wait:
                c_out.ignore_sequence(ta.sq)
                c_out.wait_sequence(res.sq)
                continue

            c_out.confirm_sequence(ta.sq)

    def __deduce_min_probability(self, probabilities):
        best = probabilities[-1]
        for i in range(len(probabilities) - 1, -1, -1):
            p = probabilities[i]
            if p <= RtMatchSequence.dynamic_trs_fine:
                break
            best = p
        return best

    def __find_executables(self, c_out):
        sequences = c_out.sequences()

        agg_transitions = AggregatedCtxTransitions()
        for sq in sequences:
            agg_transitions.append(sq.fetch_transitions())

        probabilities = agg_transitions.probabilities()
        if not probabilities:
            return []
        min_probability = self.__deduce_min_probability(probabilities)

        to_execute = []
        for tps in agg_transitions:
            sq_cloner = SequenceCloner(c_out, tps.sq)
            frozen = None
            for trs in tps.transitions:
                if min_probability <= trs.probability:
                    ta = TransitionAttempt(
                        sq=sq_cloner.get(),
                        trs=trs
                    )
                    to_execute.append(ta)
                else:
                    if frozen is None:
                        frozen = FrozenSequence(sq_cloner.get())
                        c_out.freeze(frozen)
                    frozen.append(trs)
        return to_execute

    def create_ctx(self, event_listener, owner=None):
        return MatcherContext(event_listener, owner, self.get_name())

    def get_name(self):
        return self.__name

    def get_compiled_spec(self):
        return self.__compiled_spec


class ContextEventHandler(object):
    def sequence_forked(self, ctx, sq, new_sq):
        pass

    def sequence_forking(self, ctx, sq):
        pass

    def sequence_matched(self, ctx, sq):
        pass

    def sequence_failed(self, ctx, sq):
        pass

    def sequence_res(self, ctx, res):
        pass

    def ctx_create(self, ctx):
        pass

    def ctx_complete(self, ctx):
        pass


class AwaitingEventListener(ContextEventHandler):
    def __init__(self, sq):
        self.__sq = sq

    def sequence_matched(self, ctx, sq):
        self.__sq.submatcher_matched(sq)

    def ctx_complete(self, ctx):
        self.__sq.subctx_complete(ctx)


class Context(object):
    def __init__(self, matcher, int_ctx, event_listener):
        self.__matcher = matcher
        self.__int_ctx = int_ctx
        self.__event_listener = event_listener

    def intctx(self):
        return self.__int_ctx

    def push_sentence(self, s):
        self.__int_ctx.push_sentence(s)

    def attach(self, ctx):
        self.__event_listener.attach(ctx)

    def run_until_complete(self):
        self.__matcher.process(self)


class Matcher(object):
    def __init__(self, compiled):
        self.__compiled = compiled

    def get_matcher(self, name, none_on_missing=False):
        return self.__compiled.get_matcher(name, none_on_missing=none_on_missing)

    def __find_executables(self, c_out):
        return [c for c in c_out.ctxs() if c.ctx.has_backlog()]

    def __handle_ctx(self, matcher, ctx):
        while True:
            c_out = ctx.checkout_contexts()
            exe = self.__find_executables(c_out)
            for e in exe:
                c_out.checkout(e.ctx)
                res = self.__handle_ctx(e.matcher, e.ctx)
                if res.complete:
                    c_out.complete(e.ctx)
                else:
                    c_out.confirm(e.ctx)
            c_out.commit()
            res = matcher.match(ctx)
            if ctx.empty():
                break
        return res

    def new_context(self):
        event_listener = ContextOutputDispatcher()
        event_forwarder = ContextEventsForwarder(event_listener)
        ctx_callbacks = MatcherCallbacks(self)

        intctx = MatcherContext(event_listener, ctx_callbacks, 'root-ctx')
        for m in self.__compiled.get_primary():
            intctx.create_ctx(m.get_name(), event_listener=event_forwarder)

        return Context(self, intctx, event_listener)

    def process(self, ctx):
        intctx = ctx.intctx()
        c_out = intctx.checkout_contexts()
        exe = self.__find_executables(c_out)
        for e in exe:
            c_out.checkout(e.ctx)
            res = self.__handle_ctx(e.matcher, e.ctx)
            if res.complete:
                c_out.complete(e.ctx)
            else:
                c_out.confirm(e.ctx)
        c_out.commit()


class ContextOutputDispatcher(ContextEventHandler):
    def __init__(self):
        self.__attached = []

    def attach(self, ctx):
        self.__attached.append(ctx)

    def sequence_forked(self, ctx, sq, new_sq):
        for a in self.__attached:
            a.sequence_forked(ctx, sq, new_sq)

    def sequence_forking(self, ctx, sq):
        for a in self.__attached:
            a.sequence_forking(ctx, sq)

    def sequence_matched(self, ctx, sq):
        for a in self.__attached:
            a.sequence_matched(ctx, sq)

    def sequence_failed(self, ctx, sq):
        for a in self.__attached:
            a.sequence_failed(ctx, sq)

    def sequence_res(self, ctx, res):
        for a in self.__attached:
            a.sequence_res(ctx, res)

    def ctx_create(self, ctx):
        for a in self.__attached:
            a.ctx_create(ctx)

    def ctx_complete(self, ctx):
        for a in self.__attached:
            a.ctx_complete(ctx)


class ContextEventsForwarder(ContextEventHandler):
    def __init__(self, dst_listener):
        self.__dst = dst_listener

    def sequence_forked(self, ctx, sq, new_sq):
        self.__dst.sequence_forked(ctx, sq, new_sq)

    def sequence_forking(self, ctx, sq):
        self.__dst.sequence_forking(ctx, sq)

    def sequence_matched(self, ctx, sq):
        self.__dst.sequence_matched(ctx, sq)

    def sequence_failed(self, ctx, sq):
        self.__dst.sequence_failed(ctx, sq)

    def sequence_res(self, ctx, res):
        self.__dst.sequence_res(ctx, res)

    def ctx_create(self, ctx):
        self.__dst.ctx_create(ctx)

    def ctx_complete(self, ctx):
        self.__dst.ctx_complete(ctx)


class MatcherCallbacks(object):
    def __init__(self, matcher):
        self.__matcher = matcher

    def find_matcher(self, name, none_on_missing=False):
        return self.__matcher.get_matcher(name, none_on_missing=none_on_missing)
