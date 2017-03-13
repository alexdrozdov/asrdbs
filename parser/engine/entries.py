#!/usr/bin/env python
# -*- #coding: utf8 -*-


import functools
import common.ifmodified
import parser.engine.rt
import parser.engine.matched
import parser.spare.wordform
from argparse import Namespace as ns
from common.argres import argres
from parser.spare.rules import RtRule, RtMatchString


logs_enabled = False


class RtEntry(object):
    def get_logger(self):
        return None
        return self.logger

    @argres(show_result=False)
    def __init__(self, owner, based_on):
        if isinstance(based_on, RtEntry):
            self._init_from_rtme(owner, based_on)
        elif isinstance(based_on, ns):
            self._init_from_form_spec(
                owner,
                based_on.form,
                based_on.spec_state_def,
                based_on.rtms_offset,
                based_on.attributes if hasattr(based_on, 'attributes') else {}
            )

    @argres(show_result=False)
    def _init_from_form_spec(self, owner, form, spec_state_def, rtms_offset, attributes):
        assert form is not None and spec_state_def is not None
        self._owner = owner
        self._form = form
        self._spec = spec_state_def
        self.__rtms_offset = rtms_offset
        self.__reliability = spec_state_def.get_reliability() * form.get_reliability()
        self.__attributes = attributes
        self._closed = spec_state_def.is_closed()

        self.__create_name(self._spec.get_name())
        self._create_rules()
        self._index_rules()
        self._create_static_rules()

    @argres(show_result=False)
    def _init_from_rtme(self, owner, rtme, form=None):
        if form is None:
            form = rtme._form.copy({'ro', 'w_once', 'morf'})
        self._owner = owner
        self._form = form
        self._spec = rtme._spec
        self.__rtms_offset = rtme.__rtms_offset
        self.__reliability = rtme.__reliability
        self._closed = rtme._closed

        self.__name = RtMatchString(rtme.__name)
        self.__pending = rtme.__pending[:]
        self.__copy_attributes(rtme)
        self._index_rules()
        self.__copy_matched_rules(rtme)

    @argres(show_result=False)
    def __copy_attributes(self, rtme):
        self.__attributes = {k: v for k, v in list(rtme.__attributes.items())}

    @argres(show_result=False)
    def _create_rules(self):
        self.__pending = []
        for r in self._spec.get_rt_rules():
            assert r is not None
            for b in r.get_bindings():
                if b.need_reindex():
                    self.__reindex_name(b)
            self.__pending.append(r)

    @argres(show_result=False)
    def _create_static_rules(self):
        self.__matched = []
        for r in self._spec.get_stateless_rules():
            self.__matched.append(ns(rule=r, rtme=self))

    @argres(show_result=False)
    def __copy_matched_rules(self, rtme):
        self.__matched = []
        for rule_rtme in rtme.__matched:
            self.__matched.append(
                ns(
                    rule=rule_rtme.rule.new_copy(),
                    rtme=self if id(rule_rtme) == id(rtme) else self._owner[rule_rtme.rtme.get_offset()] if rule_rtme.rtme.get_offset() < self.get_offset() else rule_rtme.rtme.get_offset()
                )
            )

    def get_matched_rules(self):
        return self.__matched

    @argres(show_result=True)
    def matched_list_valid(self):
        for rule_rtme in self.__matched:
            if isinstance(rule_rtme.rtme, RtMatchEntry):
                continue
            return False
        return True

    @argres(show_result=False)
    def resolve_matched_rtmes(self):
        for rule_rtme in self.__matched:
            if isinstance(rule_rtme.rtme, int):
                rule_rtme.rtme = self._owner[rule_rtme.rtme]
        return True

    @argres(show_result=False)
    def _index_rules(self):
        self.__required_count = 0
        for r in self.__pending:
            if not r.is_optional():
                self.__required_count += 1

    def __create_name(self, name):
        self.__name = RtMatchString(name)
        if self.__name.need_reindex():
            self.__reindex_name(self.__name)

    def __reindex_name(self, name):
        stack = self._owner.get_stack()
        if name.get_max_level() is not None:
            stack = stack[0:max(name.get_max_level() - 1, 0)]
        try:
            name.update(str(name).format(*stack))
        except IndexError:
            str_name = str(name).replace(
                '[', '\\['
            ).replace(
                ']', '\\]'
            ).replace(
                '+', '\\+'
            )
            stack = stack + ['\\d+'] * 20
            name.update(str_name.format(*stack))

    @argres()
    def __decrease_rule_counters(self, rule):
        if not rule.is_persistent():
            self.__required_count -= 1
        return self.__required_count

    def get_name(self):
        return self.__name

    def get_owner(self):
        return self._owner

    def get_form(self):
        return self._form

    def get_spec(self):
        return self._spec

    def get_offset(self, base=None):
        return self.__rtms_offset

    def get_reliability(self):
        return self.__reliability

    def closed(self):
        return self._closed

    @argres()
    def has_pending(self, required_only=False):
        if required_only:
            return self.__required_count > 0
        return len(self.__pending) > 0

    @argres(show_result=False)
    def add_link(self, link):
        self._owner.add_link(link)

    @argres()
    def find_transitions(self, forms):
        return functools.reduce(
            lambda x, y: x + list(y),
            map(
                lambda form:
                    filter(
                        lambda frm_trs: frm_trs[1].get_to().is_static_applicable(frm_trs[0]),
                        map(
                            lambda trs: (form, trs),
                            self._spec.get_transitions(filt_fcn=lambda t: not t.get_to().is_fini())
                        )
                    ),
                forms
            ),
            []
        ) + list(map(
            lambda trs: (parser.spare.wordform.SpecStateFiniForm(), trs),
            self._spec.get_transitions(filt_fcn=lambda t: t.get_to().is_fini())
        ))

    @argres()
    def handle_rules(self, on_entry=None):
        pending = []
        affected_links = []

        entries = list(map(
            lambda e: common.ifmodified.IfModified(
                e,
                lambda v: v.get_form().revision()
            ),
            [on_entry, ] if on_entry is not None
            else
            self._owner.get_entries(hidden=True, exclude=self)
        ))

        for r in self.__pending:
            applicable = False
            for e in entries:
                if self.__check_applicable(r, e.get()):
                    applicable = True
                    if not self.__apply_on(r, e.get()):
                        return ns(later=False, again=False, valid=False, affected_links=[])

                    if e.modified():
                        affected_links.extend(e.get_trackable_links())

                    self.__decrease_rule_counters(r)
                    self.__add_matched_rule(r, e.get())
                    if not r.is_persistent():
                        break
            if not applicable or r.is_persistent():
                pending.append(r)
            self.__pending = pending
        return ns(later=False, again=False, valid=True, affected_links=affected_links)

    def modified(self):
        return False

    def get_trackable_links(self):
        return self._owner.get_trackable_links(self)

    @argres(show_result=False)
    def __add_matched_rule(self, rule, rtme):
        self.__matched.append(ns(rule=rule, rtme=rtme))

    @argres()
    def __check_applicable(self, rule, other_rtme):
        if isinstance(other_rtme, RtTmpEntry):
            return False
        return rule.is_applicable(self, other_rtme)

    @argres()
    def __apply_on(self, rule, other_rtme):
        return rule.apply_on(self, other_rtme) != RtRule.res_failed

    def has_attribute(self, name):
        return name in self.__attributes

    def get_attribute(self, name):
        return self.__attributes[name]

    def __repr__(self):
        try:
            return "{0}(objid={1}, name='{2}')".format(
                self.__class__.__name__,
                hex(id(self)),
                self.get_name()
            )
        except:
            return "{0}(objid={1})".format(
                self.__class__.__name__,
                hex(id(self))
            )

    def __str__(self):
        try:
            return "{0}(objid={1}, name='{2}')".format(
                self.__class__.__name__,
                hex(id(self)),
                self.get_name()
            )
        except:
            return "{0}(objid={1})".format(
                self.__class__.__name__,
                hex(id(self))
            )


class RtMatchEntry(RtEntry):
    def __init__(self, owner, based_on):
        super().__init__(owner, based_on)

    def copy_for_owner(self, owner):
        return RtMatchEntry(owner, self)


class RtTmpEntry(RtEntry):
    @argres(show_result=False)
    def __init__(self, owner, based_on):
        super().__init__(owner, based_on)

    @argres(show_result=False)
    def _init_from_form_spec(self, owner, form, spec_state_def, rtms_offset, attributes):
        super()._init_from_form_spec(owner, form, spec_state_def, rtms_offset, attributes)
        self.__sub_ctx = None

    def copy_for_owner(self, owner):
        raise RuntimeError("RtTmpEntry doesnt allow copying")

    def _create_rules(self):
        pass

    def _index_rules(self):
        pass

    def _create_static_rules(self):
        pass

    def get_matched_rules(self):
        return []

    def get_subctx(self):
        return self.__sub_ctx

    @argres(show_result=False)
    def resolve_matched_rtmes(self):
        return True

    @argres()
    def find_transitions(self, forms):
        return list(map(
            lambda f: (f, parser.build.objects.TrsDef(
                None,
                self.get_spec(),
                st_to=self.get_spec()
            )),
            forms
        ))

    @argres()
    def handle_rules(self, on_entry=None):
        return ns(later=False, again=False, valid=True, affected_links=[])

    @argres(show_result=False)
    def set_subctx(self, sub_ctx):
        assert self.__sub_ctx is None
        self.__sub_ctx = sub_ctx

    @argres(show_result=False)
    def add_sequence_res(self, sub_ctx, res):
        rc, rtms = self.__add_sequence_res(sub_ctx, res)
        if not rc:
            return
        for new_rtms in self.__propagate_mergeable(sub_ctx, res, rtms):
            new_rtms.get_ctx().add_sequence(new_rtms)

    @argres(show_result=True)
    def __add_sequence_res(self, sub_ctx, res):
        assert sub_ctx == self.__sub_ctx
        assert res.fini
        if not res.valid:
            return False, None
        rtms = self._owner.subseq(start=0, stop=-2)
        subseq_anchor = res.sq.get_anchors()[0].get_form()
        rtme = RtMatchEntry(
            rtms,
            ns(
                form=subseq_anchor,
                spec_state_def=self._spec,
                rtms_offset=self.get_offset(),
                attributes={
                    'subseq': parser.engine.matched.MatchedSequence(res.sq)
                }
            )
        )
        return rtms.append(rtme), rtms

    def __propagate_mergeable(self, sub_ctx, res, rtms):
        new_rtmss = [rtms, ]
        assert sub_ctx == self.__sub_ctx
        assert res.fini
        if not res.valid:
            return []
        subseq_end_spec = res.sq[-2].get_spec()  # Get spec for last subseq entry
        subseq_end_form = res.sq[-2].get_form()
        seq_end_spec = rtms[-1].get_spec()       # Get spec for last seq entry
        for trs in seq_end_spec.get_transitions():  # Try to find alternate transitions
            if not subseq_end_spec.can_merge(trs.get_to()):
                continue
            new_rtms = parser.engine.rt.RtMatchSequence(rtms)
            subseq_end_form = res.sq[-2].get_form()
            rtme = RtMatchEntry(
                new_rtms,
                ns(
                    form=subseq_end_form,
                    spec_state_def=subseq_end_spec,
                    rtms_offset=self.__rtms_offset + 1,
                    attributes={
                        'merged-with': None
                    }
                )
            )
            new_rtmss.append(rtme)
        return new_rtmss

    @argres(show_result=False)
    def add_forked_sequence(self, sub_ctx, new_sq):
        assert sub_ctx == self.__sub_ctx

    @argres(show_result=False)
    def unset_subctx(self, sub_ctx):
        assert id(sub_ctx) == id(self.__sub_ctx), '{0}, {1}'.format(sub_ctx, self.__sub_ctx)
        self.__sub_ctx = None


class RtVirtualEntry(RtEntry):
    @argres(show_result=False)
    def __init__(self, owner, based_on):
        super().__init__(owner, based_on)

    @argres(show_result=False)
    def _init_from_form_spec(self, owner, form, spec_state_def, rtms_offset, attributes):
        form = parser.spare.wordform.SpecStateVirtForm()
        super()._init_from_form_spec(
            owner, form, spec_state_def,
            rtms_offset, attributes
        )

        self.__referers = []
        self.__first_handle = True
        self._closed = spec_state_def.is_closed()

    @argres(show_result=False)
    def _init_from_rtme(self, owner, rtme):
        form = parser.spare.wordform.SpecStateVirtForm(
            rtme.get_form()
        )
        super()._init_from_rtme(owner, rtme, form=form)

        self.__referers = []
        self.__first_handle = rtme.__first_handle
        self._closed = rtme._closed
        self.__copy_referers(rtme)

    def copy_for_owner(self, owner):
        return RtVirtualEntry(owner, self)

    @argres(show_result=False)
    def __copy_referers(self, rtme):
        self.__referers = []
        for referer in rtme.__referers:
            self.__referers.append(
                self._owner[referer.get_offset()] if referer.get_offset() < self.get_offset() else referer.get_offset()
            )

    @argres(show_result=False)
    def resolve_matched_rtmes(self):
        super().resolve_matched_rtmes()

        for i, referer in enumerate(self.__referers):
            if isinstance(referer, int):
                self.__referers[i] = self._owner[self.__referers[i]]

        return True

    @argres()
    def handle_rules(self, on_entry=None):
        if not self.closed():
            return ns(later=True, again=False, valid=False, affected_links=[])

        if self.__first_handle:
            self.__first_handle = False
            return ns(later=False, again=True, valid=False, affected_links=[])

        res = super().handle_rules(on_entry=on_entry)
        return res

    def close_aggregator(self):
        self._closed = True

    def has_attribute(self, name):
        return False

    def get_attribute(self, name):
        return None

    @argres()
    def attach_referer(self, rtme):
        if rtme not in self.__referers:
            self.__referers.append(rtme)
        self._form.add_form(rtme.get_form())
        return True


class SiblingSpec(object):
    def __init__(self, spec, ctx, matcher, form):
        self.__spec = spec
        self.__ctx = ctx
        self.__matcher = matcher
        self.__form = form

    def get_ctx(self):
        return self.__ctx

    def get_matcher(self):
        return self.__matcher

    def __getattr__(self, name):
        return self.__spec.__getattribute__(name)


class RtSiblingLeaderEntry(RtEntry):
    @argres(show_result=False)
    def __init__(self, owner, based_on):
        super().__init__(owner, based_on)

    @argres(show_result=False)
    def _init_from_form_spec(self, owner, form, spec_state_def,
                             rtms_offset, attributes):
        super()._init_from_form_spec(
            owner, form, spec_state_def, rtms_offset, attributes
        )

    @argres(show_result=False)
    def _init_from_rtme(self, owner, rtme, form=None):
        super()._init_from_rtme(owner, rtme, form)

    def copy_for_owner(self, owner):
        return RtSiblingLeaderEntry(owner, self)

    def close(self):
        self._closed = True

    @argres()
    def handle_rules(self, on_entry=None):
        if not self.closed():
            return ns(later=True, again=False, valid=False, affected_links=[])

        return super().handle_rules(on_entry=on_entry)

    @argres()
    def find_transitions(self, forms):
        closer_trs = self.__find_closer_transitions(forms)
        sibling_trs = self.__find_sibling_transitions(forms)

        return closer_trs + sibling_trs

    def __find_sibling_transitions(self, forms):
        follower_trs = self.__find_follower_trs()
        follower_spec = follower_trs.get_to()

        matchers = self.__deduce_possible_matchers()
        trs = []
        for m in matchers:
            ctx = m.create_ctx()
            m.once(ctx, [self.get_form(), ])
            m.once(ctx, forms)
            ctxs = ctx.split_by_sequences()
            for i_ctx in ctxs:
                head = i_ctx.get_head()
                sbln_spec = SiblingSpec(follower_spec,
                                        ctx=i_ctx, matcher=m, form=head.form)
                sbln_trs = follower_trs.copy_with_to(sbln_spec)
                trs.append((head.form, sbln_trs))
        return trs

    def __deduce_possible_matchers(self):
        res = []
        ctx = self.get_owner().get_ctx()
        for s in self._spec.get_sibling_specs():
            m = ctx.find_matcher(s)
            if m.is_applicable(self.get_form()):
                res.append(m)
        return res

    def __find_closer_transitions(self, forms):
        closer_trs = self.__find_closer_trs()
        closer = closer_trs.get_to()
        return [(form, closer_trs) for form in forms if closer.is_static_applicable(form)]

    def __find_closer_trs(self):
        for trs in self._spec.get_transitions():
            if trs.get_to().is_sibling_closer():
                return trs
        raise RuntimeError("No closer found")

    def __find_follower_trs(self):
        for trs in self._spec.get_transitions():
            if trs.get_to().is_sibling_follower():
                return trs
        raise RuntimeError("No closer found")


class RunOnceContext(object):
    def __init__(self, ctx):
        self.__ctx = ctx
        self.__complete = False
        self.__fini = False

    def was_fini(self):
        return self.__fini

    def sequence_matched(self, sq):
        self.__fini = True

    def ctx_complete(self):
        self.__complete = True

    def __getattr__(self, name):
        return self.__ctx.__getattribute__(name)


class RtSiblingFollowerEntry(RtEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__ctx = self.get_spec().get_ctx()
        self.__matcher = self.get_spec().get_matcher()

    def copy_for_owner(self, owner):
        return RtSiblingFollowerEntry(owner, self)

    @argres()
    def find_transitions(self, forms):
        sibling_trs, fini = self.__find_sibling_transitions(forms)

        if fini:
            return sibling_trs + self.__find_closer_transitions(forms)

        return sibling_trs

    def __find_sibling_transitions(self, forms):
        follower_trs = self.__find_follower_trs()

        trs = []
        ctx = RunOnceContext(self.__ctx)
        self.__matcher.once(ctx, forms)
        heads = ctx.get_heads()

        if len(heads) == 1:
            head = ctx.get_head()
            sbln_trs = follower_trs.copy_with_to(self.get_spec())
            trs.append((head.form, sbln_trs))
        elif 1 < len(heads):
            ctxs = ctx.split_by_sequences()
            for i_ctx in ctxs:
                head = i_ctx.get_head()
                sbln_spec = SiblingSpec(self.get_spec().original_spec(),
                                        ctx=i_ctx, form=head.form)
                sbln_trs = follower_trs.copy_with_to(sbln_spec)
                trs.append((head.form, sbln_trs))

        return trs, ctx.was_fini()

    def __find_closer_transitions(self, forms):
        closer_trs = self.__find_closer_trs()
        closer = closer_trs.get_to()
        return [(form, closer_trs) for form in forms if closer.is_static_applicable(form)]

    def __find_closer_trs(self):
        for trs in self._spec.get_transitions():
            if trs.get_to().is_sibling_closer():
                return trs
        raise RuntimeError("No closer found")

    def __find_follower_trs(self):
        for trs in self._spec.get_transitions():
            if trs.get_to().is_sibling_follower():
                return trs
        raise RuntimeError("No closer found")


class RtSiblingCloserEntry(RtEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @argres(show_result=False)
    def _init_from_form_spec(self, owner, form, spec_state_def,
                             rtms_offset, attributes):
        form = parser.spare.wordform.SpecStateVirtForm()
        super()._init_from_form_spec(
            owner, form, spec_state_def, rtms_offset, attributes
        )
        self.__leader_closed = False

    @argres(show_result=False)
    def _init_from_rtme(self, owner, rtme, form=None):
        form = parser.spare.wordform.SpecStateVirtForm(
            rtme.get_form()
        )
        super()._init_from_rtme(owner, rtme, form)
        self.__leader_closed = rtme.__leader_closed

    def copy_for_owner(self, owner):
        return RtSiblingCloserEntry(owner, self)

    def has_pending(self, required_only=False):
        return not self.__leader_closed

    def handle_rules(self, on_entry=None):
        if not self.__leader_closed:
            leader = self.__find_leader_entry()
            leader.close()
            self.__leader_closed = True
        return ns(later=False, again=False, valid=True, affected_links=[])

    def __find_leader_entry(self):
        sq = self.get_owner()
        self_found = True
        for e in sq.reversed():
            if id(e) == id(self):
                self_found = True
            elif e.get_spec().is_sibling_leader() and self_found:
                return e
        raise RuntimeError('Preceeding siblings leader entry not found')
