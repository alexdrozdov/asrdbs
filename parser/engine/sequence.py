import logging


import common.argres
import common.output
import parser.engine.entries
import parser.engine.events
import parser.engine.structs


from argparse import Namespace as ns
from common.argres import argres
from parser.engine.structs import NextSequenceStep, NextSequenceStepTransition, TrsResult


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
        logger = logging.getLogger(logger_name)
        formatter = logging.Formatter('%(asctime)s : %(message)s')
        fileHandler = logging.FileHandler(log_file, mode='w')
        fileHandler.setFormatter(formatter)

        logger.setLevel(level)
        logger.addHandler(fileHandler)
        return logger

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
            left = indexes[0]
            right = indexes[1]
            if right < 0:
                right += len(sq.__all_entries) + 1
            indexes = list(range(left, right))

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

    @argres()
    def __handle_fixed_trs(self, trs, form):
        to = trs.get_to()
        self.__stack.handle_trs(trs)

        rtme = parser.engine.entries.from_spec(self, to, form)

        if not self.append(rtme):
            return TrsResult(sq=self, valid=False, fini=False, again=False, wait=False)

        if to.is_fini():
            return TrsResult(sq=self, valid=self.__on_fini(), fini=True, again=False, wait=False)
        return TrsResult(sq=self, valid=True, fini=False, again=to.is_virtual(), wait=False)

    @argres()
    def __handle_dynamic_trs(self, trs, form):
        to = trs.get_to()
        sq = AwaitingSequence(self, to)
        el = parser.engine.events.AwaitingEventListener(sq)

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

    def __len__(self):
        return len(self.__all_entries)

    def reversed(self):
        sequence_length = len(self.__all_entries)
        for i in range(sequence_length - 1, -1, -1):
            yield self.__all_entries[i]


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

    def __reset_under(self, level):
        if level + 1 < len(self.__stack):
            self.__stack = self.__stack[0:level + 1]

    def __incr_level(self, level):
        assert level == len(self.__stack) or level + 1 == len(self.__stack), \
            'l={0}, len={1}, stack={2}'.format(
                level, len(self.__stack), self.__stack
            )
        if level + 1 == len(self.__stack):
            self.__stack[level] += 1
        else:
            self.__stack.append(0)
        assert level + 1 == len(self.__stack)

    def handle_trs(self, trs):
        levelpath = trs.get_levelpath()
        self.__reset_under(min(levelpath))
        for m in levelpath:
            self.__incr_level(m)

    def get_stack(self):
        return self.__stack


def new_sequence(spec, matcher, ctx):
    ini_spec = spec.get_inis()[0]
    sq = RtMatchSequence(
        ns(
            matcher=matcher,
            initial_entry=parser.engine.entries.RtMatchEntry(None, ns(
                form=parser.spare.wordform.SpecStateIniForm(),
                spec_state_def=ini_spec,
                rtms_offset=0)
            ),
            ctx=ctx,
        )
    )
    sq.backlog().fetch_master()
    ctx.add_sequence(sq)
