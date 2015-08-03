#!/usr/bin/env python
# -*- #coding: utf8 -*-


import speccmn
import specdefs.adj_noun
import specdefs.adv_adj
import specdefs.subj_predicate
import gvariant
from speccmn import RtRule
# import graph


class UniqEnum(object):
    def __init__(self):
        self.__uniq = 1

    def get_uniq(self):
        r = self.__uniq
        self.__uniq *= 2
        return r


ue = UniqEnum()


class SequenceSpecIter(object):
    def __init__(self, l):
        self.__l = l

    def get_all_entries(self):
        return self.__l

    def get_after(self, entry):
        try:
            i = self.__l.index(entry)
            return self.__l[i + 1]
        except:
            return None


class IterableSequenceSpec(speccmn.SequenceSpec):
    def __init__(self, spec):
        speccmn.SequenceSpec.__init__(self, spec.get_name())
        self.__basic_spec = spec.get_spec()
        self.__index_all_entries()
        self.__index_layers()
        self.__index_hierarchy()

    def __index_subentries(self, item, level):
        for st in item["entries"]:
            self.__set_state_uid(st)
            self.__set_state_level(st, level)
            self.__all_entries.append(st)
            if st.has_key("entries"):
                self.__index_subentries(st, level + 1)

    def __index_all_entries(self):
        self.__all_entries = []
        level = 0
        for st in self.__basic_spec:
            self.__set_state_uid(st)
            self.__set_state_level(st, level)
            self.__all_entries.append(st)
            if st.has_key("entries"):
                self.__index_subentries(st, level + 1)

    def __index_layer(self, subspec, layer=0):
        if len(self.__layers) <= layer:
            self.__layers.append([])
        l_list = self.__layers[layer]
        for st in subspec:
            l_list.append(st)
            if st.has_key("entries"):
                self.__index_layer(st["entries"], layer=layer+1)

    def __index_layers(self):
        self.__layers = []
        self.__index_layer(self.__basic_spec)

    def __set_state_uid(self, state):
        if state.has_key("uid"):
            return
        state["uid"] = ue.get_uniq()

    def __set_state_level(self, state, level):
        state["level"] = level

    def __add_child_to_parent(self, child, parent):
        self.__parents[child["uid"]] = parent

    def __index_item_entries(self, item):
        l = []
        if item.has_key("entries"):
            for st in item["entries"]:
                l.append(st)
                self.__add_child_to_parent(st, item)
                self.__index_item_entries(st)
        self.__hierarchy[item["uid"]] = l

    def __index_hierarchy(self):
        self.__hierarchy = {}
        self.__parents = {}

        basic_list = []
        for st in self.__basic_spec:
            basic_list.append(st)
            self.__index_item_entries(st)
        self.__hierarchy[None] = basic_list

    def get_level_count(self):
        return len(self.__layers)

    def get_state_iter(self):
        return SequenceSpecIter(self.__all_entries)

    def get_parent(self, item):
        return self.__parents[item["uid"]]

    def get_hierarchical_iter(self, base):
        if base is None:
            return SequenceSpecIter(self.__hierarchy[None])
        return SequenceSpecIter(self.__hierarchy[base["uid"]])

    def get_level_iter(self, level):
        return SequenceSpecIter(self.__layers[level])

    def get_child_iter(self, base):
        return self.get_hierarchical_iter(base)


class SpecCompiler(object):
    def __init__(self):
        self.__states = []
        self.__name2state = {}
        self.__containers = []
        self.__containers_qq = []
        self.__inis = []

    def gen_state_name(self, st):
        return st["id"]

    def __add_state(self, state):
        self.__states.append(state)
        self.__name2state[state.get_name()] = state
        if state.is_container():
            self.__containers.append(state)
        if state.is_init():
            self.__inis.append(state)

    def __create_states(self, spec):
        spec_iter = spec.get_state_iter()
        for st in spec_iter.get_all_entries():
            state_name = self.gen_state_name(st)
            state = SpecStateDef(state_name, st)
            if state.get_level() > 0:
                parent_st = spec.get_parent(st)
                parent_state_name = self.gen_state_name(parent_st)
                state.set_parent_state(self.__name2state[parent_state_name])
            self.__add_state(state)

    def __create_downgrading_trs(self, spec):
        deepest = spec.get_level_count()

        if deepest < 2:
            return

        for level in range(deepest - 2, -1, -1):  # -2 = -1 -1 - Enumerated from zero and no need to build downgrading trs for deepest level
            spec_iter = spec.get_level_iter(level)
            for st in spec_iter.get_all_entries():
                state = self.__name2state[self.gen_state_name(st)]
                child_iter = spec.get_child_iter(st)
                for c_st in child_iter.get_all_entries():
                    c_state = self.__name2state[self.gen_state_name(c_st)]
                    if c_state.is_container():
                        state.add_trs_to_child_child(c_state)
                    state.add_trs_to_child(c_state)
                    if c_state.is_required():
                        break

    def __create_single_level_trs(self, spec, base=None):
        spec_iter = spec.get_hierarchical_iter(base)

        for st in spec_iter.get_all_entries():
            state = self.__name2state[self.gen_state_name(st)]
            st_next = st
            while True:
                st_next = spec_iter.get_after(st_next)
                if st_next is None:
                    break
                state_next = self.__name2state[self.gen_state_name(st_next)]
                state.add_trs_to_neighbour(state_next)
                if state_next.is_container():
                    state.add_trs_to_neighbours_childs(state_next)
                if state_next.is_required():
                    break  # No need to add anything further - we cant skip this state
            if state.is_repeated():
                state.add_trs_to_self()
            if state.is_container():
                self.__add_container_to_process(state)

    def __create_upper_level_trs(self, spec):
        self.__create_single_level_trs(spec, base=None)

    def __add_container_to_process(self, state):
        if state not in self.__containers_qq:
            self.__containers_qq.append(state)

    def __create_lower_level_trs(self, spec):
        self.__containers_qq = [c for c in self.__containers]
        while len(self.__containers_qq):
            container = self.__containers_qq[0]
            self.__containers_qq = self.__containers_qq[1:]
            st = container.get_spec()
            self.__create_single_level_trs(spec, st)

    def __eval_local_final(self, spec):
        self.__containers_qq = [c for c in self.__containers]
        while len(self.__containers_qq):
            container = self.__containers_qq[0]
            self.__containers_qq = self.__containers_qq[1:]
            st = container.get_spec()
            spec_iter = spec.get_hierarchical_iter(st)

            sts = [i for i in spec_iter.get_all_entries()]
            sts.reverse()
            for s in sts:
                state = self.__name2state[self.gen_state_name(s)]
                state.set_local_final()
                if state.is_required():
                    break

    def __create_upgrading_trs(self, spec):
        spec_iter = spec.get_state_iter()
        for st in spec_iter.get_all_entries():
            state = self.__name2state[self.gen_state_name(st)]
            if state.is_contained() and state.is_local_final():
                parent = state.get_parent_state()
                state.add_parent_trs(parent)
                while parent.is_contained() and parent.is_local_final():
                    parent = parent.get_parent_state()
                    state.add_parent_trs(parent)

    def __remove_containers(self):
        states = []
        for state in self.__states:
            if state.is_container():
                state.unlink_all()
                continue
            states.append(state)
        self.__states = states

    def __merge_transitions(self):
        for state in self.__states:
            state.merge_transitions()

    def __create_state_rules(self):
        for state in self.__states:
            state.create_rules()

    def compile(self, spec):
        self.__spec_name = spec.get_name()

        spec = IterableSequenceSpec(spec)
        self.__create_states(spec)
        self.__create_downgrading_trs(spec)
        self.__create_upper_level_trs(spec)
        self.__create_lower_level_trs(spec)
        self.__eval_local_final(spec)
        self.__create_upgrading_trs(spec)
        self.__remove_containers()
        self.__merge_transitions()
        self.__create_state_rules()

        cs = CompiledSpec(spec, self.__spec_name, self.__states, self.__inis)
        return cs


class SpecStateDef(object):
    def __init__(self, name, spec_dict, parent=None):
        self.__name = name
        self.__transitions = []
        self.__neighbour_transitions = []
        self.__child_transitions = []
        self.__rtransitions = []
        self.__spec_dict = spec_dict
        self.__parent = parent
        self.__is_container = spec_dict.has_key("entries")
        self.__is_contained = False
        if self.__parent:
            self.__is_contained = True
        self.__is_required = spec_dict.has_key("required") and spec_dict["required"]
        self.__is_repeatable = spec_dict.has_key("repeatable") and spec_dict["repeatable"]
        self.__is_local_final = False
        self.__is_init = spec_dict.has_key("fsm") and spec_dict["fsm"] == speccmn.FsmSpecs.init
        self.__is_fini = spec_dict.has_key("fsm") and spec_dict["fsm"] == speccmn.FsmSpecs.fini
        self.__uid = ue.get_uniq()

        self.__stateless_rules = []
        self.__rt_rules = []

    def get_name(self):
        return self.__name

    def get_spec(self):
        return self.__spec_dict

    def get_uid(self):
        return self.__uid

    def is_init(self):
        return self.__is_init

    def is_fini(self):
        return self.__is_fini

    def is_container(self):
        return self.__is_container

    def is_contained(self):
        return self.__is_contained

    def is_local_final(self):
        return self.__is_local_final

    def is_required(self):
        return self.__is_required

    def is_repeated(self):
        return self.__is_repeatable

    def get_parent_state(self):
        return self.__parent

    def get_level(self):
        return self.__spec_dict["level"]

    def set_parent_state(self, parent):
        self.__parent = parent
        self.__is_contained = True

    def set_local_final(self):
        self.__is_local_final = True

    def add_trs_to_self(self):
        pass

    def add_trs_to_neighbour(self, to):
        if to not in self.__neighbour_transitions:
            self.__neighbour_transitions.append(to)
        to.__add_trs_from(self)

    def add_trs_to_child(self, to):
        if to not in self.__child_transitions:
            self.__child_transitions.append(to)
        to.__add_trs_from(self)

    def add_trs_to_child_child(self, child):
        for to in child.__child_transitions:
            self.add_trs_to_child(to)
            to.__add_trs_from(self)

    def add_trs_to_neighbours_childs(self, item):
        for to in item.__child_transitions:
            if to not in self.__neighbour_transitions:
                self.__neighbour_transitions.append(to)
            to.__add_trs_from(self)

    def add_parent_trs(self, parent):
        for to in parent.__neighbour_transitions:
            if to not in self.__neighbour_transitions:
                self.__neighbour_transitions.append(to)
            to.__add_trs_from(self)
        if parent.is_repeated():
            self.add_trs_to_neighbours_childs(parent)
            self.add_trs_to_neighbour(parent)

    def __add_trs_from(self, t_from):
        if t_from not in self.__rtransitions:
            self.__rtransitions.append(t_from)

    def unlink_all(self):
        for to in self.__neighbour_transitions:
            to.unlink_from(self)
        for to in self.__child_transitions:
            to.unlink_from(self)
        for t_from in self.__rtransitions:
            t_from.unlink_to(self)
        self.__neighbour_transitions = []
        self.__child_transitions = []
        self.__rtransitions = []
        self.__transitions = []

    def unlink_from(self, t_from):
        self.__rtransitions.remove(t_from)

    def unlink_to(self, to):
        if to in self.__neighbour_transitions:
            self.__neighbour_transitions.remove(to)
        if to in self.__child_transitions:
            self.__child_transitions.remove(to)
        if to in self.__transitions:
            self.__transitions.remove(to)

    def merge_transitions(self):
        self.__transitions = []
        for to in self.__neighbour_transitions:
            if to not in self.__transitions:
                self.__transitions.append(to)
        for to in self.__child_transitions:
            if to not in self.__transitions:
                self.__transitions.append(to)

    def __create_rule_list(self, is_static, rule_list, target_list):
        for r in rule_list:
            if self.__spec_dict.has_key(r):
                rule_def = self.__spec_dict[r]
                if isinstance(rule_def, list):
                    for rd in rule_def:
                        target_list.append(RtRule(rd, is_static))
                else:
                    target_list.append(RtRule(rule_def, is_static))

    def __create_stateless_rules(self):
        self.__create_rule_list(True, ['pos_type'], self.__stateless_rules)

    def __create_rt_rules(self):
        self.__create_rule_list(False, ['position', 'master-slave', 'unwanted-links'], self.__rt_rules)

    def create_rules(self):
        self.__create_stateless_rules()
        self.__create_rt_rules()

    def get_transitions(self):
        return self.__transitions

    def is_static_applicable(self, form):
        for r in self.__stateless_rules:
            if not r.matched(form):
                return False
        return True

    def get_rt_rules(self):
        return [rt.new_copy() for rt in self.__rt_rules]


class CompiledSpec(object):
    def __init__(self, src_spec, name, states, inis):
        self.__src_spec = src_spec
        assert states, 'Spec without states'
        assert inis, 'Spec without init states'
        self.__states = states
        self.__inis = inis
        self.__name = name

    def get_name(self):
        return self.__name

    def get_states(self):
        return self.__states

    def get_inis(self):
        return self.__inis


class RtMatchSequence(gvariant.Sequence):
    def __init__(self, matcher, initial_entry=None):
        self.__matcher = matcher
        self.__entries = []
        if initial_entry is not None:
            self.__entries.append(initial_entry)
        self.__matched = 0
        self.__pending = 0
        self.__status = RtRule.res_none
        self.__pending_rules = {}
        self.__unwanted_links = []

    def clone(self):
        rtms = RtMatchSequence(self.__matcher)
        prev = None
        for e in self.__entries:
            prev = e.clone(rtms, prev=prev)
            assert prev.get_owner() == rtms
            rtms.__entries.append(prev)
        assert len(self.__entries) == len(rtms.__entries)
        return rtms

    def dismiss(self, reason=None):
        self.__status = RtRule.res_failed
        self.__matcher.dismiss(self, reason)

    def confirm_match_entry(self, rtentry):
        not_confirmed = [True for rtmes in self.__pending_rules.values() if rtentry in rtmes]
        assert not not_confirmed
        self.__matched += 1
        self.__pending -= 1

    def handle_form(self, form):
        head = self.__entries[-1]
        trs = head.find_transitions(form)
        if not trs:
            return False, []
        new_sq = []
        for t in trs[0:-1]:
            trms = self.clone()
            alive, fini = trms.__handle_trs(t, form)
            if alive:
                new_sq.append(trms)
            if fini:
                pass

        t = trs[-1]
        alive, fini = self.__handle_trs(t, form)
        return alive, new_sq

    def is_registered(self, rule, rtentry):
        return self.__pending_rules.has_key(rule) and rtentry in self.__pending_rules[rule]

    def register_rule_handler(self, rule, rtentry):
        assert rule is not None, 'Rule is None'
        assert isinstance(rule, RtRule), 'Rule is not RtRule'

        if self.__pending_rules.has_key(rule):
            rr = self.__pending_rules[rule]
        else:
            rr = []

        assert rtentry not in rr

        rr.append(rtentry)
        self.__pending_rules[rule] = rr

    def unregister_rule_handler(self, rule, rtentry):
        if self.__pending_rules.has_key(rule):
            rr = self.__pending_rules[rule]
        else:
            return
        rr.remove(rtentry)
        if rr:
            self.__pending_rules[rule] = rr
        else:
            self.__pending_rules.pop(rule)

    def __handle_trs(self, to, form):
        prev = self.__entries[-1] if self.__entries else None
        if to.is_fini():
            rtme = RtMatchEntry(self, speccmn.SpecStateFiniForm(), to, prev=prev)
            self.__entries.append(rtme)

            if not self.__handle_pending_rules(rtme):
                return False, True

            self.__handle_fini()
            return False, True
        else:
            rtme = RtMatchEntry(self, form, to, prev=prev)
            self.__entries.append(rtme)
            if rtme.has_pending():
                self.__pending += 1
            else:
                self.__matched += 1
            if not self.__handle_pending_rules(rtme):
                return False, False
        return True, False

    def __handle_fini(self):
        if self.__pending:
            self.__status = RtRule.res_failed
        else:
            self.__status = RtRule.res_matched

    def __handle_pending_rules(self, rtentry):
        for rule, rtmes in self.__pending_rules.items():
            for rtme in rtmes:
                if not rule.is_applicable(rtme, rtentry):
                    continue
                res = rule.apply_on(rtme, rtentry)
                if res == RtRule.res_failed:
                    return False
                rtme.confirm_rule(rule)
        return True

    def get_rule_name(self):
        return self.__matcher.get_name()

    def is_complete(self):
        return self.__status != RtRule.res_none and self.__status != RtRule.res_continue

    def is_valid(self):
        # if self.__pending and self.__status != RtRule.res_none and self.__status != RtRule.res_continue:
        #     for k, v in self.__pending_rules.items():
        #         print k, k.get_int_rule(),
        #         for e in v:
        #             print e.get_name(),
        # print ""
        return self.__pending == 0

    def finalize(self, valid):
        pass

    def print_sequence(self):
        print self.get_rule_name(), '<',
        for e in self.__entries:
            f = e.get_form()
            print f.get_word(),
        print '>'

    def add_required_link(self, link):
        pass

    def get_unwanted_links(self):
        return []


class SpecMatcher(object):
    def __init__(self, owner, compiled_spec, matched_cb=None):
        self.__owner = owner
        self.__compiled_spec = compiled_spec
        self.__matched_cb = matched_cb
        self.__name = self.__compiled_spec.get_name()
        self.reset()

    def reset(self):
        self.__sequences = []
        self.__rtentry2sequence = {}
        self.__is_running = False

    def is_waiting(self):
        return not self.__is_running

    def match(self, forms):
        self.__is_running = True
        for form in forms:
            self.__handle_sequences(form)
        if not self.__sequences:
            self.__is_running = False

    def __create_ini_rtentry(self):
        ini_spec = self.__compiled_spec.get_inis()[0]
        self.__sequences = [RtMatchSequence(self, RtMatchEntry(None, speccmn.SpecStateIniForm(), ini_spec, None))]

    def __handle_sequence_list(self, form):
        next_sequences = []
        for sq in self.__sequences:
            alive, new_sq = sq.handle_form(form)
            if new_sq:
                next_sequences.extend(new_sq)
            if alive:
                next_sequences.append(sq)
            if sq.is_valid() and sq.is_complete() and self.__matched_cb:
                self.__matched_cb(sq)
        self.__sequences = next_sequences

    def __handle_sequences(self, form):
        ini_rtentry_created = False
        if not self.__sequences:
            self.__create_ini_rtentry()
            ini_rtentry_created = True

        self.__handle_sequence_list(form)

        if not self.__sequences and not ini_rtentry_created:
            self.__create_ini_rtentry()
            self.__handle_sequence_list(form)

        # print ">>>"
        # self.__print_sequences()
        # print "<<<"

    def __print_sequences(self):
        for sq in self.__sequences:
            sq.print_sequence()

    def dismiss(self, sequence, reason=None):
        if sequence in self.__sequences:
            self.__sequences.remove(sequence)

    def get_name(self):
        return self.__name


class SequenceSpecMatcher(object):
    def __init__(self):
        self.__specs = []
        self.__create_specs()

    def __create_specs(self):
        # self.add_spec(specdefs.adj_noun.AdjNounSequenceSpec())
        # self.add_spec(specdefs.adv_adj.AdvAdjSequenceSpec())
        self.add_spec(specdefs.subj_predicate.SubjectPredicateSequenceSpec())

    def reset(self):
        for sp in self.__specs:
            sp.reset()

    def add_spec(self, base_spec_class):
        sc = SpecCompiler()
        spec = sc.compile(base_spec_class)
        self.__specs.append(SpecMatcher(self, spec, self.add_matched))

    def match_graph(self, graph):
        self.__matched_specs = []
        forms = graph.get_forms()
        for sp in self.__specs:
            sp.match(forms)
            sp.match([speccmn.SpecStateFiniForm()])
        return self.__matched_specs

    def add_matched(self, sq):
        self.__matched_specs.append(sq)


class RtMatchEntry(object):
    def __init__(self, owner, form, spec_state_def, prev=None, do_not_init_rules=False):
        assert form is not None, "Form is required"
        assert spec_state_def is not None, "Spec is required"
        self.__owner = owner
        self.__form = form
        self.__spec = spec_state_def
        self.__status = RtRule.res_none
        self.__next = None
        self.__prev = prev

        if prev is not None:
            prev.__next = self

        self.__matched = []
        self.__pending_count = 0
        if not do_not_init_rules:
            self.__pending = self.__spec.get_rt_rules()
            self.__register_pending_rules()
        else:
            self.__pending = []

    def get_name(self):
        return self.__spec.get_name()

    def get_owner(self):
        return self.__owner

    def __register_pending_rules(self):
        self.__pending_count = 0
        for r in self.__pending:
            assert r is not None
            if not r.ignore_pending_state():
                self.__pending_count += 1
            self.__owner.register_rule_handler(r, self)

    def clone(self, owner, prev=None):
        rtme = RtMatchEntry(owner, self.__form, self.__spec, prev, do_not_init_rules=True)
        rtme.__status = self.__status
        if prev is not None:
            prev.__next = rtme

        rtme.__matched = [m for m in self.__matched]
        rtme.__pending = [p.clone() for p in self.__pending]
        rtme.__register_pending_rules()
        return rtme

    def find_transitions(self, form):
        trs = []
        for t in self.__spec.get_transitions():
            if t.is_static_applicable(form):
                trs.append(t)
        return trs

    def confirm_rule(self, rule):
        self.__pending.remove(rule)
        if not rule.ignore_pending_state():
            self.__pending_count -= 1

        if self.__owner.is_registered(rule, self):
            self.__owner.unregister_rule_handler(rule, self)
        self.__matched.append(rule)

        if not self.__pending_count:
            if self.__pending:
                for r in self.__pending:
                    if self.__owner.is_registered(r, self):
                        self.__owner.unregister_rule_handler(r, self)
            self.__status = RtRule.res_matched
            self.__owner.confirm_match_entry(self)

    def dismiss(self, reason=None):
        if self.__prev is not None:
            self.__prev.__dismiss_prev()
        if self.__next:
            self.__next.__dismiss_next()
        self.__unregister_pending_rules()
        self.__owner.dismiss(self)
        self.__next = None
        self.__prev = None

    def has_pending(self):
        return self.__pending_count > 0

    def __unregister_pending_rules(self):
        for r in self.__pending:
            self.__owner.unregister_rule_handler(r, self)
        self.__pending = []

    def __dismiss_next(self):
        if self.__next:
            self.__next.__dismiss_next()
        self.__unregister_pending_rules()
        self.__next = None

    def __dismiss_prev(self):
        if self.__prev:
            self.__prev.__dismiss_prev()
        self.__unregister_pending_rules()
        self.__prev = None

    def get_form(self):
        return self.__form

    def get_spec(self):
        return self.__spec

    def add_unwanted_link(self, l):
        self.__owner.add_unwanted_link(l)


# anss = specdefs.subj_predicate.SubjectPredicateSequenceSpec()
# sc = SpecCompiler()
# res = sc.compile(anss)
#
# g = graph.SpecGraph(img_type='svg')
# file_name = 'imgs/sp-{0}.svg'.format(0)
# g.generate(res.get_states(), file_name)
