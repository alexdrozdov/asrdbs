#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import json
import copy
import common.config
import parser.lang.common
import parser.lang.defs
from parser.lang.common import RtRule, RtMatchString
import parser.preprocessor
import parser.matcher
import graph
import common.output
from argparse import Namespace as ns
import logging
import sentparser


logs_enabled = False


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


class IterableSequenceSpec(parser.lang.common.SequenceSpec):
    def __init__(self, spec):
        parser.lang.common.SequenceSpec.__init__(self, spec.get_name())
        spec = copy.deepcopy(spec)
        self.__unroll_repeatable_entries(spec.get_spec())
        self.__index_all_entries()
        self.__index_layers()
        self.__index_hierarchy()
        self.__validate = spec.get_validate()

    def get_validate(self):
        return self.__validate

    def __index_subentries(self, item, level):
        if item.has_key("entries"):
            for st in item["entries"]:
                self.__set_state_uid(st)
                self.__set_state_level(st, level)
                self.__all_entries.append(st)
                if st.has_key("entries") or st.has_key("uniq-items"):
                    self.__index_subentries(st, level + 1)
        if item.has_key("uniq-items"):
            for st in item["uniq-items"]:
                self.__set_state_uid(st)
                self.__set_state_level(st, level)
                self.__all_entries.append(st)
                if st.has_key("entries") or st.has_key("uniq-items"):
                    self.__index_subentries(st, level + 1)

    def __index_all_entries(self):
        self.__all_entries = []
        level = 0
        for st in self.__basic_spec:
            self.__set_state_uid(st)
            self.__set_state_level(st, level)
            self.__all_entries.append(st)
            if st.has_key("entries") or st.has_key("uniq-items"):
                self.__index_subentries(st, level + 1)

    def __create_entry_copy(self, entry, order, set_order=False, repeatable=False, required=False):
        entry = copy.deepcopy(entry)
        if set_order:
            entry["id"] += "[{0}]".format(order)
        entry["repeatable"] = repeatable
        entry["required"] = required
        if entry.has_key("entries"):
            entries = []
            for st in entry["entries"]:
                sub_specs = self.__unroll_entry(st)
                entries.extend(sub_specs)
            entry["entries"] = entries
        if entry.has_key("uniq-items"):
            entries = []
            for st in entry["uniq-items"]:
                sub_specs = self.__unroll_entry(st)
                entries.extend(sub_specs)
            entry["uniq-items"] = entries
        return entry

    def __unroll_entry(self, entry):
        if not entry.has_key("repeatable") or not isinstance(entry["repeatable"], tuple):
            return [copy.deepcopy(entry), ]

        min_count = entry["repeatable"][0]
        max_count = entry["repeatable"][1]

        if min_count is None:
            return []

        res = []
        if (min_count == max_count and min_count == 1) or (min_count == 0 and max_count == 1):
            set_order = False
        else:
            set_order = True
        i = 0
        if min_count == max_count:
            for i in range(min_count):
                res.append(self.__create_entry_copy(entry, i, repeatable=False, required=True, set_order=set_order))
            return res

        if min_count:
            for i in range(min_count):
                res.append(self.__create_entry_copy(entry, i, repeatable=False, required=True, set_order=set_order))

        if max_count:
            for i in range(min_count, max_count):
                res.append(self.__create_entry_copy(entry, i, repeatable=False, required=False, set_order=set_order))
        else:
            order = '{$GLEVEL}'
            res.append(self.__create_entry_copy(entry, order, repeatable=True, required=False, set_order=set_order))

        return res

    def __unroll_repeatable_entries(self, basic_spec):
        new_spec = []
        for st in basic_spec:
            sub_specs = self.__unroll_entry(st)
            new_spec.extend(sub_specs)
        self.__basic_spec = new_spec

    def __index_layer(self, subspec, layer=0):
        if len(self.__layers) <= layer:
            self.__layers.append([])
        l_list = self.__layers[layer]
        for st in subspec:
            l_list.append(st)
            if st.has_key("entries"):
                self.__index_layer(st["entries"], layer=layer+1)
            if st.has_key("uniq-items"):
                self.__index_layer(st["uniq-items"], layer=layer+1)

    def __index_layers(self):
        self.__layers = []
        self.__index_layer(self.__basic_spec)

    def __set_state_uid(self, state):
        if state.has_key("uid"):
            return
        state["uid"] = str(uuid.uuid1())

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
        if item.has_key("uniq-items"):
            for st in item["uniq-items"]:
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
        if self.__parents.has_key(item["uid"]):
            return self.__parents[item["uid"]]
        return None

    def get_hierarchical_iter(self, base):
        if base is None:
            return SequenceSpecIter(self.__hierarchy[None])
        return SequenceSpecIter(self.__hierarchy[base["uid"]])

    def get_level_iter(self, level):
        return SequenceSpecIter(self.__layers[level])

    def get_child_iter(self, base):
        return self.get_hierarchical_iter(base)


class SpecCompiler(object):
    def __init__(self, owner=None, stack=None, level=0, reliability=1.0):
        self.__owner = owner
        self.__stack = stack if stack is not None else []
        self.__level = level
        self.__reliability = reliability
        self.__states = []
        self.__name2state = {}
        self.__containers = []
        self.__anchor_containers = []
        self.__containers_qq = []
        self.__inis = []
        self.__finis = []
        self.__incapsulate_in = []
        self.__rule_bindins = {}
        self.__local_spec_anchors = []

    def __create_parent_path(self, st):
        parent = self.__spec.get_parent(st)
        if parent is not None:
            return self.gen_state_name(parent)
        else:
            path = '::' + self.__spec_name
            if self.__parent_spec_name:
                path = self.__parent_spec_name + path
        return path

    def __create_spec_path(self):
        path = '::' + self.__spec_name
        if self.__parent_spec_name:
            path = self.__parent_spec_name + path
        return path

    def gen_state_name(self, st):
        return self.resolve_name(st, st['id'])

    def resolve_variant_count(self, ref_state, name):
        if '$LOCAL_SPEC_ANCHOR' in name:
            return len(self.__local_spec_anchors)
        return 1

    def resolve_name(self, ref_state, name, var_num=None):
        if '$LEVEL' in name:
            name = name.replace('$LEVEL', str(ref_state['level']))
        if '$GLEVEL' in name:
            name = name.replace('$GLEVEL', str(ref_state['level'] + self.__level))
        if '$LOCAL_SPEC_ANCHOR' in name:
            assert self.__local_spec_anchors, 'Tried to resolve name for spec "{0}" without local spec anchor'.format(
                self.__spec_name
            )
            assert len(self.__local_spec_anchors) == 1 or var_num is not None, 'Tried to resolve name for spec "{0}" with multiple local spec anchors {1}'.format(
                self.__spec_name,
                self.__local_spec_anchors
            )
            if var_num is None:
                name = name.replace('$LOCAL_SPEC_ANCHOR', str(self.__local_spec_anchors[0].get_name()))
            else:
                name = name.replace('$LOCAL_SPEC_ANCHOR', str(self.__local_spec_anchors[var_num].get_name()))
        if '$INCAPSULATED' in name:
            assert ref_state.has_key('include') and len(ref_state['include']) == 1
            name = name.replace('$INCAPSULATED', ref_state['include'][0])
        if '$THIS' in name:
            assert '$THIS' not in ref_state['id'], 'Recursive name with $THIS spec'
            this_path = self.gen_state_name(ref_state)
            name = name.replace('$THIS', this_path)
        if '$PARENT' in name:
            assert name.find('$PARENT') == 0, '$PARENT must be first'
            parent_path = self.__create_parent_path(ref_state)
            name = name.replace('$PARENT', parent_path)
        elif '$SPEC' in name:
            assert name.find('$SPEC') == 0, '$SPEC must be first'
            spec_path = self.__create_spec_path()
            name = name.replace('$SPEC', spec_path)
        elif name.find('::') != 0:
            print "Compile warning: $-definition is missing for", self.__spec_name, name
        return name

    def __add_state(self, state):
        self.__states.append(state)
        self.__name2state[str(state.get_name())] = state
        if state.is_container() or state.is_uniq_container():
            self.__containers.append(state)
        if state.is_init():
            self.__inis.append(state)
        if state.is_fini():
            self.__finis.append(state)
        if state.includes_spec():
            self.__incapsulate_in.append(state)

    def __handle_anchor_state(self, state):
        if state.is_container() or state.is_uniq_container():
            return

        if state.includes_spec():
            in_spec = state.get_included()
            in_spec_anchors = in_spec.get_local_spec_anchors()
            if in_spec_anchors:
                self.__local_spec_anchors.extend(in_spec_anchors)
            return

        self.__local_spec_anchors.append(state)

    def __create_states(self, spec):
        spec_iter = spec.get_state_iter()
        for st in spec_iter.get_all_entries():
            state_name = self.gen_state_name(st)
            state = SpecStateDef(self, state_name, st)
            if state.get_level() > 0:
                parent_st = spec.get_parent(st)
                parent_state_name = str(self.gen_state_name(parent_st))
                parent_state = self.__name2state[parent_state_name]
                state.set_parent_state(parent_state)
                if parent_state.is_anchor():
                    state.force_anchor()
                state.inherit_parent_reliability(parent_state.get_reliability())
            else:
                state.inherit_parent_reliability(self.get_reliability())

            if state.has_include():
                if self.__spec_depth <= 1 or state.include_is_static_only():
                    in_spec_name = state.get_include_name()
                    in_spec = self.__owner.get_spec(in_spec_name)
                    compiler = SpecCompiler(
                        owner=self.__owner,
                        stack=self.__stack,
                        level=state.get_glevel() + 1,
                        reliability=state.get_reliability()
                    )
                    compiled_in_spec = compiler.compile(in_spec, parent_spec_name=str(state.get_name()))
                    state.set_incapsulated_spec(compiled_in_spec)
                else:
                    state.set_dynamic()

            if state.is_anchor():
                self.__handle_anchor_state(state)

            self.__add_state(state)

    def __create_downgrading_trs(self, spec):
        deepest = spec.get_level_count()

        if deepest < 2:
            return

        for level in range(deepest - 2, -1, -1):  # -2 = -1 -1 - Enumerated from zero and no need to build downgrading trs for deepest level
            spec_iter = spec.get_level_iter(level)
            for st in spec_iter.get_all_entries():
                state = self.__name2state[str(self.gen_state_name(st))]
                child_iter = spec.get_child_iter(st)
                for c_st in child_iter.get_all_entries():
                    c_state = self.__name2state[str(self.gen_state_name(c_st))]
                    if any((
                        c_state.is_container(),
                        c_state.is_uniq_container(),
                        state.can_merge(c_state))
                    ):
                        state.add_trs_to_child_child(c_state)
                    state.add_trs_to_child(c_state)
                    if c_state.is_required() and state.is_container():
                        break

    def __create_single_level_trs(self, spec, base=None):
        spec_iter = spec.get_hierarchical_iter(base)

        for st in spec_iter.get_all_entries():
            state = self.__name2state[str(self.gen_state_name(st))]
            st_next = st
            while True:
                st_next = spec_iter.get_after(st_next)
                if st_next is None:
                    break
                state_next = self.__name2state[str(self.gen_state_name(st_next))]
                state.add_trs_to_neighbour(state_next)
                if state_next.is_container() or state_next.is_uniq_container():
                    state.add_trs_to_neighbours_childs(state_next)
                if state_next.is_required():
                    break  # No need to add anything further - we cant skip this state
            if state.is_repeated():
                state.add_trs_to_self()
            if state.is_container() or state.is_uniq_container():
                self.__add_container_to_process(state)

    def __create_upper_level_trs(self, spec):
        self.__create_single_level_trs(spec, base=None)

    def __add_container_to_process(self, state):
        if state not in self.__containers_qq:
            self.__containers_qq.append(state)

    def __create_lower_level_trs(self, spec):
        self.__containers_qq = [c for c in self.__containers if c.is_container()]
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

            if container.is_container():
                sts.reverse()
                for s in sts:
                    state = self.__name2state[str(self.gen_state_name(s))]
                    state.set_local_final()
                    if state.is_required():
                        break
            else:
                for s in sts:
                    state = self.__name2state[str(self.gen_state_name(s))]
                    state.set_local_final()

    def __create_upgrading_trs(self, spec):
        spec_iter = spec.get_state_iter()
        for st in spec_iter.get_all_entries():
            state = self.__name2state[str(self.gen_state_name(st))]
            if state.is_contained() and state.is_local_final():
                parent = state.get_parent_state()
                state.add_parent_trs(parent)
                while parent.is_contained() and parent.is_local_final():
                    parent = parent.get_parent_state()
                    state.add_parent_trs(parent)

    def __remove_containers(self):
        states = []
        for state in self.__states:
            if state.is_container() or state.is_uniq_container():
                state.unlink_all()
                continue
            states.append(state)
        self.__states = states

    def __merge_transitions(self):
        for state in self.__states:
            state.merge_transitions()

    def __create_state_rules(self):
        for state in self.__states:
            if state.has_noncreated_rules():
                state.create_rules(self)

    def __incapsulate_rules(self):
        for state in self.__incapsulate_in:
            if not state.has_rules():
                continue
            in_spec = state.get_included()
            for in_spec_anchor in in_spec.get_local_spec_anchors():
                assert in_spec_anchor is not None
                rules_to_incapsulate = state.get_rules_list()
                in_spec_anchor.extend_rules(rules_to_incapsulate, state.get_glevel())

    def __incapsulate_states(self):
        for state in self.__incapsulate_in:
            compiled_in_spec = state.get_included()
            ini = compiled_in_spec.get_inis()
            assert len(ini) == 1
            fini = compiled_in_spec.get_finis()
            assert len(fini) == 1
            for in_state in compiled_in_spec.get_states():
                if in_state.is_init() or in_state.is_fini():
                    continue
                self.__states.append(in_state)
                self.__name2state[str(in_state.get_name())] = in_state
            for trs in ini[0].get_transitions():
                for r_trs in state.get_rtransitions():
                    t_from = r_trs.get_from()
                    t_from.add_trs_to(trs, with_trs=r_trs)
            for r_trs in fini[0].get_rtransitions():
                t_from = r_trs.get_from()
                for trs in state.get_transitions():
                    t_from.add_trs_to(trs)
            ini[0].unlink_all()
            fini[0].unlink_all()
            state.unlink_all()
            self.__states.remove(state)

    def __review_anchors(self):
        for state in self.__states:
            if not state.is_anchor():
                continue
            if state not in self.__local_spec_anchors:
                state.force_anchor(is_anchor=False)

    def register_rule_binding(self, rule, binding):
        return

    def binding_needs_resolve(self, binding):
        assert isinstance(binding, RtMatchString)
        if self.__name2state.has_key(str(binding)):
            state = self.__name2state[str(binding)]
            if not state.is_container() and not state.is_uniq_container() and not state.includes_spec():
                return False
            return True
        raise RuntimeError('state name matching not implemented')

    def resolve_binding(self, binding):
        assert isinstance(binding, RtMatchString)
        if self.__name2state.has_key(str(binding)):
            state = self.__name2state[str(binding)]
            if state.is_container():
                raise RuntimeError('$LOCAL_LEVEL_ANCHOR not implemented for containers')
                return
            if state.is_uniq_container():
                raise RuntimeError('$LOCAL_LEVEL_ANCHOR not implemented for uniq containers')
                return
            if state.includes_spec():
                in_spec = state.get_included()
                in_spec_anchors = in_spec.get_local_spec_anchors()
                assert in_spec_anchors is not None and len(in_spec_anchors) == 1
                return in_spec_anchors[0].get_name()
        raise RuntimeError('state name matching not implemented')

    def compile(self, spec, parent_spec_name=''):
        self.__parent_spec_name = parent_spec_name
        self.__spec_name = spec.get_name()
        self.__stack.append(self.__spec_name)
        self.__spec_depth = self.__stack.count(self.__spec_name)

        spec = IterableSequenceSpec(spec)
        self.__spec = spec
        self.__create_states(spec)
        self.__create_downgrading_trs(spec)
        self.__create_upper_level_trs(spec)
        self.__create_lower_level_trs(spec)
        self.__eval_local_final(spec)
        self.__create_upgrading_trs(spec)
        self.__remove_containers()
        self.__merge_transitions()
        self.__incapsulate_rules()
        self.__incapsulate_states()
        self.__create_state_rules()
        self.__review_anchors()

        cs = CompiledSpec(
            spec,
            self.__spec_name,
            self.__states,
            self.__inis,
            self.__finis,
            self.__local_spec_anchors,
            spec.get_validate() if self.__level == 0 else None
        )
        self.__stack.pop()
        return cs

    def get_level(self):
        return self.__level

    def get_reliability(self):
        return self.__reliability


class TrsDef(object):
    def __init__(self, compiler, st_from, restrict_default=None, st_to=None, trs_to=None, with_trs=None):
        assert restrict_default is None
        assert compiler is None
        assert st_to is not None or trs_to is not None
        if st_to is not None:
            self.__init_from_stto(compiler, st_from, st_to)
        else:
            self.__init_from_trsto(compiler, st_from, trs_to, with_trs)
        assert self.__levelpath and isinstance(self.__levelpath, tuple)

    def __init_from_stto(self, compiler, st_from, st_to):
        assert isinstance(st_to, SpecStateDef)
        self.__from = st_from
        self.__to = st_to
        if self.__from.get_glevel() == self.__to.get_glevel():
            self.__levelpath = [self.__to.get_glevel(), ]
        elif self.__from.get_glevel() > self.__to.get_glevel():
            self.__levelpath = [self.__to.get_glevel(), ]  # to is higher than from. Anything below to doesnt matter
        else:
            self.__levelpath = range(self.__from.get_glevel() + 1, self.__to.get_glevel() + 1)
        self.__levelpath = tuple(self.__levelpath)

    def __init_from_trsto(self, compiler, st_from, trs_to, with_trs):
        assert isinstance(trs_to, TrsDef)
        self.__from = st_from
        self.__to = trs_to.get_to()

        if with_trs is not None:
            upper_level = min(trs_to.get_from().get_glevel(), with_trs.get_to().get_glevel(), with_trs.__levelpath[0])
        else:
            upper_level = trs_to.get_from().get_glevel()

        if self.__from.get_glevel() == upper_level:
            self.__levelpath = [upper_level, ]
        elif self.__from.get_glevel() > upper_level:
            self.__levelpath = [upper_level, ]
        else:
            self.__levelpath = range(self.__from.get_glevel() + 1, upper_level + 1)

        if upper_level < trs_to.get_from().get_glevel():
            self.__levelpath.extend(range(upper_level + 1, trs_to.get_from().get_glevel()))

        self.__levelpath.extend(trs_to.__levelpath)
        to_level = trs_to.get_to().get_glevel()
        self.__levelpath = tuple(sorted(filter(lambda x: x <= to_level, list(set(self.__levelpath)))))

    def get_to(self):
        return self.__to

    def get_from(self):
        return self.__from

    def get_levelpath(self):
        return self.__levelpath

    def unlink(self, must_exists=True):
        self.__from.remove_trs(self, must_exists=must_exists)
        if self.__to is not self.__from:
            self.__to.remove_trs(self, must_exists=must_exists)

    def __cmp__(self, other):
        assert isinstance(other, TrsDef)
        if self == other:
            return 0
        return cmp(id(self), id(other))

    def __eq__(self, other):
        assert isinstance(other, TrsDef)
        return self.__from == other.__from and self.__to == other.__to and self.__levelpath == other.__levelpath

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'TrsDef(from={0}, to={1}, levelpath={2})'.format(str(self.__from), str(self.__to), self.__levelpath)

    def __hash__(self):
        return hash(self.__repr__())


class SpecStateDef(object):

    static_rules = ['pos_type', 'case']
    dynamic_rules = ['same-as', 'position', 'master-slave', 'unwanted-links', 'refers-to']
    all_rules = static_rules + dynamic_rules

    def __init__(self, compiler, name, spec_dict, parent=None):
        self.__name = RtMatchString(name)
        if self.__name.need_resolve():
            self.__name.update(compiler.resolve_name(spec_dict, str(self.__name)))
        self.__transitions = []
        self.__neighbour_transitions = []
        self.__child_transitions = []
        self.__rtransitions = []
        self.__spec_dict = spec_dict
        self.__parent = parent
        self.__is_container = spec_dict.has_key("entries")
        self.__is_uniq_container = spec_dict.has_key("uniq-items")
        self.__is_contained = False
        if self.__parent:
            self.__is_contained = True
        self.__is_required = spec_dict.has_key("required") and spec_dict["required"]
        self.__is_repeatable = spec_dict.has_key("repeatable") and spec_dict["repeatable"]
        self.__is_local_final = False
        self.__is_init = spec_dict.has_key("fsm") and spec_dict["fsm"] == parser.lang.defs.FsmSpecs.init
        self.__is_fini = spec_dict.has_key("fsm") and spec_dict["fsm"] == parser.lang.defs.FsmSpecs.fini
        self.__is_virtual = spec_dict.has_key("virtual") and spec_dict["virtual"]
        self.__uid = str(uuid.uuid1())
        if spec_dict.has_key('include'):
            self.__incapsulate_spec_name = spec_dict['include']['spec']
            self.__static_only_include = spec_dict['include']['static-only'] if spec_dict['include'].has_key('static-only') else False
        else:
            self.__incapsulate_spec_name = None
            self.__static_only_include = False
        self.__incapsulate_spec = None
        self.__stateless_rules = []
        self.__rt_rules = []
        self.__level = spec_dict['level']
        self.__glevel = compiler.get_level() + self.__level
        self.__is_local_anchor = spec_dict.has_key('anchor')
        self.__transitions_merged = False
        self.__add_to_seq = spec_dict['add-to-seq'] if spec_dict.has_key('add-to-seq') else True
        self.__reliability = spec_dict['reliability'] if spec_dict.has_key('reliability') else 1.0
        self.__merges_with = set(spec_dict['merges-with']) if spec_dict.has_key('merges-with') else set()
        self.__fixed = True

    def get_name(self):
        return self.__name

    def get_spec(self):
        return self.__spec_dict

    def get_level(self):
        return self.__level

    def get_glevel(self):
        return self.__glevel

    def get_reliability(self):
        return self.__reliability

    def get_uid(self):
        return self.__uid

    def is_init(self):
        return self.__is_init

    def is_fini(self):
        return self.__is_fini

    def is_container(self):
        return self.__is_container

    def is_uniq_container(self):
        return self.__is_uniq_container

    def is_contained(self):
        return self.__is_contained

    def is_local_final(self):
        return self.__is_local_final

    def is_required(self):
        return self.__is_required

    def is_repeated(self):
        return self.__is_repeatable

    def is_anchor(self):
        return self.__is_local_anchor

    def is_virtual(self):
        return self.__is_virtual

    def fixed(self):
        return self.__fixed

    def force_anchor(self, is_anchor=True):
        self.__is_local_anchor = is_anchor

    def can_merge(self, other):
        return bool(self.__merges_with & other.__merges_with)

    def inherit_parent_reliability(self, reliability):
        self.__reliability *= reliability

    def get_parent_state(self):
        return self.__parent

    def set_parent_state(self, parent):
        self.__parent = parent
        self.__is_contained = True

    def set_local_final(self):
        self.__is_local_final = True

    def add_to_seq(self):
        return self.__add_to_seq

    def __append_neighbour_trs(self, trs):
        assert isinstance(trs, TrsDef)
        if trs not in self.__neighbour_transitions:
            self.__neighbour_transitions.append(trs)
            trs.get_to().__add_trs_from(trs)
            if self.can_merge(trs.get_to()):
                for ntrs in trs.get_to().__child_transitions:
                    self.__append_neighbour_trs(TrsDef(None, self, trs_to=ntrs))
                for ntrs in trs.get_to().__neighbour_transitions:
                    self.__append_neighbour_trs(TrsDef(None, self, trs_to=ntrs))

    def __append_child_trs(self, trs):
        assert isinstance(trs, TrsDef)
        if trs not in self.__child_transitions:
            self.__child_transitions.append(trs)
            trs.get_to().__add_trs_from(trs)
            if self.can_merge(trs.get_to()):
                for ntrs in trs.get_to().__child_transitions:
                    self.__append_child_trs(TrsDef(None, self, trs_to=ntrs))
                for ntrs in trs.get_to().__neighbour_transitions:
                    self.__append_child_trs(TrsDef(None, self, trs_to=ntrs))

    def __append_trs(self, trs):
        assert isinstance(trs, TrsDef)
        if trs not in self.__transitions:
            self.__transitions.append(trs)
            trs.get_to().__add_trs_from(trs)
            if self.can_merge(trs.get_to()):
                for ntrs in trs.get_to().__child_transitions:
                    self.__append_trs(TrsDef(None, self, trs_to=ntrs))
                for ntrs in trs.get_to().__neighbour_transitions:
                    self.__append_trs(TrsDef(None, self, trs_to=ntrs))
                for ntrs in trs.get_to().__transitions:
                    self.__append_trs(TrsDef(None, self, trs_to=ntrs))

    def add_trs_to(self, trs, with_trs=None):
        self.__append_trs(TrsDef(None, self, trs_to=trs, with_trs=with_trs))

    def add_trs_to_self(self):
        self.add_trs_to_neighbour(self)

    def add_trs_to_neighbour(self, to):
        self.__append_neighbour_trs(TrsDef(None, self, st_to=to))

    def add_trs_to_child(self, to):
        self.__append_child_trs(TrsDef(None, self, st_to=to))

    def add_trs_to_child_child(self, child):
        for trs in child.__child_transitions:
            self.__append_child_trs(TrsDef(None, self, trs_to=trs))

    def add_trs_to_neighbours_childs(self, item):
        for trs in item.__child_transitions:
            self.__append_neighbour_trs(TrsDef(None, self, trs_to=trs))

    def add_parent_trs(self, parent):
        for trs in parent.__neighbour_transitions:
            self.__append_neighbour_trs(TrsDef(None, self, trs_to=trs))
        if parent.is_repeated():
            self.add_trs_to_neighbours_childs(parent)
            self.add_trs_to_neighbour(parent)

    def __add_trs_from(self, trs):
        assert isinstance(trs, TrsDef)
        if trs not in self.__rtransitions:
            self.__rtransitions.append(trs)

    def unlink_all(self):
        for trs in set(self.__rtransitions + self.__transitions):
            trs.unlink(must_exists=True)
        for to_trs in self.__neighbour_transitions[:]:
            to_trs.unlink(must_exists=False)
        for to_trs in self.__child_transitions[:]:
            to_trs.unlink(must_exists=False)

        assert not self.__neighbour_transitions and not self.__child_transitions and not self.__rtransitions and not self.__transitions, 'trs={0}, rtrs={1}'.format(repr(self.__transitions), repr(self.__rtransitions))

    def remove_trs(self, trs, must_exists):
        assert isinstance(trs, TrsDef)
        assert trs.get_from() is self or trs.get_to() is self
        if trs in self.__neighbour_transitions:
            self.__neighbour_transitions.remove(trs)
        if trs in self.__child_transitions:
            self.__child_transitions.remove(trs)

        removed = False
        if trs in self.__transitions:
            self.__transitions.remove(trs)
            removed = True
        if trs in self.__rtransitions:
            self.__rtransitions.remove(trs)
            removed = True
        assert not must_exists or not self.__transitions_merged or removed, '{0} -> {1}'.format(trs.get_from().get_name(), trs.get_to().get_name())

    def merge_transitions(self):
        self.__transitions_merged = True
        for trs in self.__neighbour_transitions:
            self.__append_trs(trs)
        for trs in self.__child_transitions:
            self.__append_trs(trs)

        assert len(self.__transitions) == len(set(self.__transitions)), self.__transitions

    def __create_rule_list(self, compiler, is_static, rule_list, target_list):
        for r in rule_list:
            if self.__spec_dict.has_key(r):
                rule_def = self.__spec_dict[r]
                if isinstance(rule_def, list):
                    for rd in rule_def:
                        if rd.created():
                            continue
                        target_list.extend(rd.create(compiler, self))
                else:
                    if not rule_def.created():
                        target_list.extend(rule_def.create(compiler, self))

    def __create_stateless_rules(self, comiler):
        self.__create_rule_list(
            comiler,
            True,
            SpecStateDef.static_rules,
            self.__stateless_rules
        )

    def __create_rt_rules(self, compiler):
        self.__create_rule_list(
            compiler,
            False,
            SpecStateDef.dynamic_rules,
            self.__rt_rules
        )

    def create_rules(self, compiler):
        self.__create_stateless_rules(compiler)
        self.__create_rt_rules(compiler)

    def has_noncreated_rules(self):
        for r in SpecStateDef.all_rules:
            if self.__spec_dict.has_key(r):
                rule_def = self.__spec_dict[r]
                if isinstance(rule_def, list):
                    for rd in rule_def:
                        if not rd.created():
                            return True
                else:
                    if not rule_def.created():
                        return True
        return False

    def get_transitions(self, filt_fcn=None):
        if filt_fcn is None:
            return self.__transitions[:]
        return filter(
            filt_fcn,
            self.__transitions
        )

    def get_rtransitions(self):
        return self.__rtransitions[:]

    def is_static_applicable(self, form):
        for r in self.__stateless_rules:
            if not r.match(form):
                return False
        return True

    def extend_rules(self, rules, max_level):
        for r, rule_def in rules.items():
            if not isinstance(rule_def, list):
                rule_def = [rule_def, ]
            rule_def = [parser.lang.common.RtRuleFactory(rr, max_level=max_level) for rr in rule_def]
            for rr in rule_def:
                assert not rr.created()
            if not self.__spec_dict.has_key(r):
                self.__spec_dict[r] = rule_def
            else:
                if isinstance(self.__spec_dict[r], list):
                    self.__spec_dict[r].extend(rule_def)
                else:
                    rule_def.extend(self.__spec_dict[r])
                    self.__spec_dict[r] = rule_def

    def get_rt_rules(self):
        return [rt.new_copy() for rt in self.__rt_rules]

    def get_rules_ro(self):
        rules = [rt for rt in self.__rt_rules]
        for r in self.__stateless_rules:
            rules.append(r)
        return rules

    def get_stateless_rules(self):
        return [r.new_copy() for r in self.__stateless_rules]

    def has_rules(self):
        return len(set(SpecStateDef.all_rules).intersection(self.__spec_dict.keys())) > 0

    def has_rt_rules(self):
        return len(set(SpecStateDef.dynamic_rules).intersection(self.__spec_dict.keys())) > 0

    def get_rules_list(self):
        return {r: self.__spec_dict[r] for r in SpecStateDef.all_rules if self.__spec_dict.has_key(r)}

    def get_rt_rules_list(self):
        return {r: self.__spec_dict[r] for r in SpecStateDef.dynamic_rules if self.__spec_dict.has_key(r)}

    def includes_spec(self):
        return self.__incapsulate_spec is not None

    def has_include(self):
            return self.__incapsulate_spec_name is not None

    def get_include_name(self):
        assert self.__incapsulate_spec_name is not None
        return self.__incapsulate_spec_name

    def include_is_static_only(self):
        return self.__static_only_include

    def set_incapsulated_spec(self, spec):
        assert self.__incapsulate_spec is None
        self.__incapsulate_spec = spec

    def get_included(self):
        return self.__incapsulate_spec

    def set_dynamic(self):
        self.__fixed = False

    def __repr__(self):
        return "SpecStateDef(name='{0}')".format(self.get_name())

    def __str__(self):
        return "SpecStateDef(name='{0}')".format(self.get_name())


class CompiledSpec(object):
    def __init__(self, src_spec, name, states, inis, finis, local_spec_anchors, validator):
        self.__src_spec = src_spec
        self.__name = name
        assert states, 'Spec without states'
        assert inis, 'Spec without init states'
        assert local_spec_anchors, 'Tried to create CompiledSpec "{0}" without any anchor'.format(self.__name)
        self.__states = states
        self.__inis = inis
        self.__finis = finis
        self.__local_spec_anchors = local_spec_anchors
        self.__validator = validator

    def get_name(self):
        return self.__name

    def get_states(self):
        return self.__states

    def get_inis(self):
        return self.__inis

    def get_finis(self):
        return self.__finis

    def get_local_spec_anchors(self):
        assert self.__local_spec_anchors, '"{0}" spec doesnt have anchor'.format(self.__name)
        return self.__local_spec_anchors

    def get_validate(self):
        return self.__validator


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
        assert l == len(self.__stack) or l + 1 == len(self.__stack), 'l={0}, len={1}, stack={2}'.format(l, len(self.__stack), self.__stack)
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


class RtSequenceLinkEntry(object):
    def __init__(self, based_on):
        if isinstance(based_on, ns):
            self.__init_on_spec(based_on.rule, based_on.link, based_on.weight)
        elif isinstance(based_on, RtSequenceLinkEntry):
            self.__init_on_rsle(based_on)
        else:
            raise ValueError('Unsupported initializer')

    def __init_on_spec(self, rule, link, weight):
        assert isinstance(link, sentparser.Link)
        assert link.get_master() is not None and link.get_slave() is not None
        self.__rule = rule
        self.__link = link
        self.__weight = weight

    def __init_on_rsle(self, rsle):
        assert isinstance(rsle.__link, sentparser.Link)
        assert rsle.__link.get_master() is not None and rsle.__link.get_slave() is not None
        self.__rule = rsle.__rule
        self.__link = rsle.__link
        self.__weight = rsle.__weight

    def get_link(self):
        return self.__link

    def get_master(self):
        return self.__link.get_master()

    def get_slave(self):
        return self.__link.get_slave()

    def get_weight(self):
        return self.__weight

argres_level = 0


def argres(show_result=True, repr_result=None):
    def argres_internal(func):
        "This decorator dumps out the arguments passed to a function before calling it"
        argnames = func.func_code.co_varnames[:func.func_code.co_argcount]
        fname = func.func_name

        def argres_fcn(*args, **kwargs):
            obj = args[0]
            logger = obj.get_logger()
            global argres_level
            argres_level += 1
            space = '  ' * argres_level
            if logger is not None:
                s = '>>{0}{1}: {2}'.format(space, fname, ', '.join(
                    '%s=%r' % entry
                    for entry in zip(argnames, args) + kwargs.items()))
                logger.info(s)
            res = func(*args, **kwargs)
            if logger is not None and show_result:
                s = '<<{0}{1}: {2}'.format(space, fname, res if repr_result is None else repr_result(res))
                logger.info(s)
            argres_level -= 1
            return res

        if logs_enabled:
            return argres_fcn
        return func
    return argres_internal


def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__"):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict(
            [(key, todict(value, classkey))
             for key, value in obj.__dict__.iteritems()
             if not callable(value) and not key.startswith('_')
             ]
        )
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


class Link(object):
    def __init__(self, master, slave, details):
        self.__uniq = str(uuid.uuid1())
        self.__master = master
        self.__slave = slave
        self.__details = details

    def get_uniq(self):
        return self.__uniq

    def get_csum(self):
        return '{0}{1}'.format(self.__master.get_uniq(), self.__slave.get_uniq())

    def get_details(self):
        return self.__details

    def get_master(self):
        return self.__master

    def get_slave(self):
        return self.__slave

    def export_dict(self):
        return {
            'from': self.__master.get_uniq(),
            'to': self.__slave.get_uniq(),
            'udata': todict(self.__details),
        }


class MatchedEntry(object):
    def __init__(self, me, rtme=None):
        if isinstance(me, (RtMatchEntry, RtVirtualEntry)):
            self.__init_from_rtme(me)
        else:
            self.__init_from_me(me, rtme)

    def __init_from_rtme(self, rtme):
        self.__form = rtme.get_form()
        self.__name = rtme.get_name()
        self.__reliability = rtme.get_reliability()
        self.__is_hidden = not rtme.get_spec().add_to_seq()
        self.__rules = [mr.rule for mr in rtme.get_matched_rules()]
        self.__is_anchor = rtme.get_spec().is_anchor()
        self.__masters = []
        self.__slaves = []
        self.__masters_csum = set()
        self.__slaves_csum = set()

    def __init_from_me(self, me, rtme):
        assert rtme is not None
        self.__form = me.__form
        self.__name = me.__name
        self.__reliability = me.__reliability
        self.__is_hidden = me.__is_hidden
        self.__rules = [r for r in me.__rules]
        self.__is_anchor = me.__is_anchor and rtme.get_spec().is_anchor()
        if me.__is_anchor:
            self.__rules += [mr.rule for mr in rtme.get_matched_rules()]
        self.__masters = []
        self.__slaves = []
        self.__masters_csum = set()
        self.__slaves_csum = set()

    def export_dict(self):
        return {
            'uniq': self.get_uniq(),
            'udata': {
                'name': str(self.__name),
                'position': self.__form.get_position(),
                'word': self.__form.get_word(),
                'reliability': self.__reliability,
                'hidden': self.__is_hidden,
                'anchor': self.__is_anchor,
                'form': self.__form.get_info(),
            },
        }

    def get_name(self):
        return self.__name

    def get_form(self):
        return self.__form

    def get_links(self, hidden=False):
        return self.__links

    def get_uniq(self):
        return self.__form.get_uniq()

    def is_hidden(self):
        return self.__is_hidden

    def is_anchor(self):
        return self.__is_anchor

    def get_reliability(self):
        return self.__reliability

    def add_link(self, link):
        assert isinstance(link, Link)
        assert link.get_master() == self or link.get_slave() == self
        if link.get_master() == self:
            self.__slaves.append(link)
            self.__slaves_csum.add(link.get_uniq())
        else:
            self.__masters.append(link)
            self.__masters_csum.add(link.get_uniq())

    def get_master_links(self):
        return self.__masters

    def get_slave_links(self):
        return self.__slaves

    def get_masters(self):
        return [l.get_from() for l in self.__masters]

    def get_slaves(self):
        return [l.get_to() for l in self.__slaves]

    def get_rules(self):
        return self.__rules


class MatchedSequence(object):
    def __init__(self, sq):
        self.__name = sq.get_rule_name()
        self.__entries = []
        self.__all_entries = []
        self.__anchors = []
        self.__links = []
        self.__all_links = []
        self.__entries_csum = set()
        self.__links_csum = set()
        self.__uid2me = {}
        self.__reliability = 1.0

        for e in sq.get_entries(hidden=True):
            if e.has_attribute('subseq'):
                self.__copy_subseq(e)
                continue
            me = MatchedEntry(e)
            self.__append_entries(me)
            self.__reliability *= me.get_reliability()

        for master, slaves in sq.get_links().items():
            for slave, details in slaves.items():
                self.__mk_link(master, slave, details)

    def __copy_subseq(self, rtme):
        for me in rtme.get_attribute('subseq').get_entries(hidden=True):
            if isinstance(
                me.get_form(),
                (
                    parser.lang.common.SpecStateIniForm,
                    parser.lang.common.SpecStateFiniForm
                )
            ):
                continue
            me = MatchedEntry(me, rtme)
            self.__append_entries(me)
        for me in rtme.get_attribute('subseq').get_entries(hidden=True):
            if isinstance(
                me.get_form(),
                (
                    parser.lang.common.SpecStateIniForm,
                    parser.lang.common.SpecStateFiniForm
                )
            ):
                continue
            for link in me.get_master_links():
                master = link.get_master()
                slave = link.get_slave()
                me_from = self.__uid2me[master.get_form().get_uniq()]
                me_to = self.__uid2me[slave.get_form().get_uniq()]
                l = Link(me_from, me_to, link.get_details())
                me_from.add_link(l)
                me_to.add_link(l)
                self.__append_links(l)

    def __mk_link(self, master, slave, details):
        assert all((
            isinstance(master, (RtMatchEntry, RtVirtualEntry)),
            isinstance(slave, RtMatchEntry),
            isinstance(details, list)
        )), '{0}, {1}, {2}'.format(type(master), type(slave), type(details))
        me_from = self.__uid2me[master.get_form().get_uniq()]
        me_to = self.__uid2me[slave.get_form().get_uniq()]
        l = Link(me_from, me_to, details)
        me_from.add_link(l)
        me_to.add_link(l)
        self.__append_links(l)

    def __append_entries(self, me):
        self.__all_entries.append(me)
        if not me.is_hidden():
            self.__entries.append(me)
        if me.is_anchor():
            self.__anchors.append(me)
        self.__uid2me[me.get_uniq()] = me
        self.__entries_csum.add(me.get_uniq())

    def __append_links(self, link):
        if not link.get_master().is_hidden() and not link.get_slave().is_hidden():
            self.__links.append(link)
        self.__all_links.append(link)
        self.__links_csum.add(link.get_csum())

    def get_name(self):
        return self.__name

    def get_entries(self, hidden=False):
        return self.__all_entries if hidden else self.__entries

    def get_links(self, hidden=False):
        return self.__all_links if hidden else self.__links

    def get_entry_count(self, hidden=False):
        return len(self.get_entries(hidden=hidden))

    def get_reliability(self):
        return self.__reliability

    def print_sequence(self):
        print self.get_name(), '<',
        for e in self.__all_entries:
            f = e.get_form()
            if not e.is_hidden():
                print f.get_word(),
            else:
                print '<', f.get_word(), '>',
        print 'reliability={0}, entries_csum={1}, links_csum={2}>'.format(
            self.get_reliability(),
            self.__entries_csum,
            self.__links_csum
        )

    def export_dict(self):
        nodes = map(
            lambda e: e.export_dict(),
            self.__all_entries
        )
        edges = map(
            lambda l: l.export_dict(),
            self.__all_links
        )
        return {
            'name': self.__name,
            'reliability': self.__reliability,
            'nodes': nodes,
            'edges': edges,
        }

    def __repr__(self):
        r = u"MatchedSequence(objid={0}, entries=[{1}])".format(
            hex(id(self)),
            u', '.join(map(lambda x: x.get_form().get_word(), self.__entries))
        )
        return r.encode('utf-8')

    def __str__(self):
        return "MatchedSequence(objid={0})".format(hex(id(self)))

    def __eq__(self, other):
        assert isinstance(other, MatchedSequence)
        if id(self) == id(other):
            return True
        return all((self.__entries_csum == other.__entries_csum,
                    self.__links_csum == other.__links_csum,))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(
            (
                tuple(sorted(self.__entries_csum)),
                tuple(sorted(self.__links_csum))
            )
        )


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
            target: fcns[source] if fcns.has_key(source) else default_fcn for source, target, default_fcn in MatcherContext.fcns_map
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
        if logs_enabled:
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
            indexes = range(l, r)

        self.__copy_all_entries(sq, indexes=indexes)
        self.__copy_links(sq, indexes=indexes)
        # self.__copy_anchors(sq, indexes=indexes)

        sq.__ctx.sequence_forked(sq, self)

    def __copy_all_entries(self, sq, indexes):
        for i, e in filter(
            lambda (idx, entry): indexes is None or idx in indexes,
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
        for master, slaves in sq.__links.items():
            master_offset = master.get_offset()
            if indexes is not None and master_offset not in indexes:
                continue
            my_master = self[master_offset]
            self.__links[my_master] = {}
            for slave, details in slaves.items():
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

        trs_sqs = [self, ] + map(lambda x: RtMatchSequence(self), trs[0:-1])
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

        if not rtme.handle_rules():
            return False

        for e in self.get_entries(hidden=True, exclude=rtme):
            if not e.handle_rules(on_entry=rtme):
                return False

        return True

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
            ctx_create_fcn=lambda(sub_ctx, ): self.__subctx_create(sub_ctx, rte),
            sequence_res_fcn=lambda (sub_ctx, res): self.__submatcher_res(sub_ctx, rte, res),
            sequence_forked_fcn=lambda (sub_ctx, sq, new_sq): self.__submatcher_forked(sub_ctx, sq, new_sq, rte),
            ctx_complete_fcn=lambda (sub_ctx, ): self.__subctx_complete(sub_ctx, rte)
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
        print self.get_rule_name(), '<',
        for e in self.__entries:
            f = e.get_form()
            print f.get_word(),
        print '>'

    def get_links(self):
        return self.__links

    @argres(show_result=False)
    def add_link(self, links):
        assert isinstance(links, list)
        for l in links:
            assert isinstance(l, ns)
            try:
                self.__extend_link(l)
            except KeyError:
                self.__mk_link(l)

    @argres(show_result=False)
    def __mk_link(self, l):
        if not self.__links.has_key(l.master):
            self.__links[l.master] = {}
        self.__links[l.master][l.slave] = [l.details, ]

    @argres(show_result=False)
    def __extend_link(self, l):
        self.__links[l.master][l.slave].append(l.details)

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
        assert owner is not None and isinstance(compiled_spec, CompiledSpec)
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
                        form=parser.lang.common.SpecStateIniForm(),
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


class SequenceMatchRes(object):
    def __init__(self, sqs):
        self.__sqs = sqs

    def get_sequences(self):
        return self.__sqs

    def export_obj(self):
        return map(
            lambda s: s.export_dict(),
            self.__sqs
        )

    def export_json(self):
        return json.dumps(
            self.export_obj()
        )


class SequenceSpecMatcher(object):
    def __init__(self, export_svg=False, primary='sentence'):
        self.__primary_spec = 'sentence' if primary is None else primary
        self.__matchers = []
        self.__primary = []
        self.__spec_by_name = {}
        self.__matcher_by_name = {}
        self.__preprocessor = parser.preprocessor.Preprocessor()
        self.__load_linkdefs()
        self.__create_specs()
        if export_svg:
            self.__export_svg()

    def __load_linkdefs(self):
        parser.matcher.load()

    def __load_module(self, path):
        parts = ['parser', 'lang'] + path.split('/')
        root = parts[0]
        parts = parts[1:]
        path = root
        obj = __import__(root, globals(), locals(), root)
        for p in parts:
            path += '.' + p
            obj = __import__(str(path), globals(), locals(), str(path))
        return obj

    def __create_specs(self):
        cfg = common.config.Config()
        for specdefs_dir in cfg['/parser/specdefs']:
            obj = self.__load_module(specdefs_dir)
            for sd in obj.load_specdefs():
                self.add_spec(sd())
        self.build_specs()

    def __is_primary(self, name):
        return name == self.__primary_spec

    def add_spec(self, base_spec_class):
        assert base_spec_class.get_name() not in self.__spec_by_name
        res = self.__preprocessor.preprocess(base_spec_class)
        self.__spec_by_name[base_spec_class.get_name()] = ns(
            base_spec_class=base_spec_class,
            matcher=None,
            dependencies=res.dependencies
        )

    def get_spec(self, base_spec_name):
        return self.__spec_by_name[base_spec_name].base_spec_class

    def get_matcher(self, name):
        return self.__matcher_by_name[name]

    def __build_spec(self, name):
        desc = self.__spec_by_name[name]
        if desc.matcher is not None:
            return
        desc.matcher = "Build in progress"
        for d in desc.dependencies:
            self.__build_spec(d)

        sc = SpecCompiler(self)
        spec = sc.compile(desc.base_spec_class)
        matcher = SpecMatcher(self, spec)
        desc.matcher = matcher
        self.__matchers.append(matcher)
        self.__matcher_by_name[matcher.get_name()] = matcher
        if self.__is_primary(matcher.get_name()):
            self.__primary.append(matcher)

    def build_specs(self):
        for spec_name in self.__spec_by_name.keys():
            if self.__is_primary(spec_name):
                self.__build_spec(spec_name)

    def __export_svg(self):
        for sp in self.__matchers:
            g = graph.SpecGraph(img_type='svg')
            spec_name = sp.get_name()
            file_name = common.output.output.get_output_file('specs', '{0}.svg'.format(spec_name))
            g.generate(sp.get_compiled_spec().get_states(), file_name)

    def __select_most_complete(self, ctx):
        max_entries = reduce(
            lambda prev_max, msq:
                msq.get_entry_count(hidden=False) if prev_max < msq.get_entry_count(hidden=False) else prev_max,
            ctx.matched_sqs,
            0
        )
        ctx.matched_sqs = filter(lambda msq: max_entries <= msq.get_entry_count(hidden=False), ctx.matched_sqs)

    def __create_initial_ctxs(self, ctx):
        ctx.ctxs = map(
            lambda m: (
                m,
                MatcherContext(
                    ctx,
                    '__root',
                    sequence_matched_fcn=lambda (sq_ctx, sq): ctx.matched_sqs.add(sq),
                )
            ),
            self.__primary
        )

    def __create_ctx(self):
        return ns(
            matched_sqs=set(),
            find_matcher=lambda name: self.get_matcher(name)
        )

    def __handle_ctx(self, matcher, ctx, s):
        ctx.clear_new_ctxs()

        next_subctxs = []
        for mtchr, m_ctx in ctx.get_ctxs():
            # print "Processing existing sub ctxs", m_ctx, s[0].get_word(), "with", mtchr.get_name()
            res = self.__handle_ctx(mtchr, m_ctx, s)
            if not res.complete:
                next_subctxs.append((mtchr, m_ctx))
        ctx.set_ctxs(next_subctxs)

        # print "Processing ctx", ctx, s[0].get_word(), "with", matcher.get_name()
        res = matcher.match(ctx, s)
        if res.complete:
            return res

        for mtchr, m_ctx in ctx.get_new_ctxs():
            # print "Processing newly created ctxs", m_ctx, s[0].get_word(), "with", mtchr.get_name()
            self.__handle_ctx(mtchr, m_ctx, s)

        return ns(complete=False)

    def match_sentence(self, sentence, ctx=None, most_complete=False):
        if ctx is None:
            ctx = self.__create_ctx()
            self.__create_initial_ctxs(ctx)

        sentence += [parser.lang.common.SentenceFini(), ]

        for s in sentence:
            # print "==========================", s.get_word(), "===================="
            s = [s, ]
            for matcher, m_ctx in ctx.ctxs:
                self.__handle_ctx(matcher, m_ctx, s)

        if most_complete:
            self.__select_most_complete(ctx)
        smr = SequenceMatchRes(ctx.matched_sqs)
        return smr


class RtMatchEntry(object):
    def __new__(cls, *args, **kwargs):
        obj = super(RtMatchEntry, cls).__new__(cls)
        owner = args[0]
        obj.logger = owner.get_logger() if owner is not None else None
        return obj

    def get_logger(self):
        return self.logger

    @argres(show_result=False)
    def __init__(self, owner, based_on):
        if isinstance(based_on, RtMatchEntry):
            self.__init_from_rtme(owner, based_on)
        elif isinstance(based_on, ns):
            self.__init_from_form_spec(
                owner,
                based_on.form,
                based_on.spec_state_def,
                based_on.rtms_offset,
                based_on.attributes if hasattr(based_on, 'attributes') else {}
            )

    @argres(show_result=False)
    def __init_from_form_spec(self, owner, form, spec_state_def, rtms_offset, attributes):
        assert form is not None and spec_state_def is not None
        self.__owner = owner
        self.__form = form
        self.__spec = spec_state_def
        self.__rtms_offset = rtms_offset
        self.__reliability = spec_state_def.get_reliability() * form.get_reliability()
        self.__attributes = attributes

        self.__create_name(self.__spec.get_name())
        self.__create_rules()
        self.__index_rules()
        self.__create_static_rules()

    @argres(show_result=False)
    def __init_from_rtme(self, owner, rtme):
        self.__owner = owner
        self.__form = rtme.__form
        self.__spec = rtme.__spec
        self.__rtms_offset = rtme.__rtms_offset
        self.__reliability = rtme.__reliability

        self.__name = RtMatchString(rtme.__name)
        self.__pending = rtme.__pending[:]
        self.__copy_attributes(rtme)
        self.__index_rules()
        self.__copy_matched_rules(rtme)

    @argres(show_result=False)
    def __copy_attributes(self, rtme):
        self.__attributes = {k: v for k, v in rtme.__attributes.items()}

    @argres(show_result=False)
    def __create_rules(self):
        self.__pending = []
        for r in self.__spec.get_rt_rules():
            assert r is not None
            for b in r.get_bindings():
                if b.need_reindex():
                    self.__reindex_name(b)
            self.__pending.append(r)

    @argres(show_result=False)
    def __create_static_rules(self):
        self.__matched = []
        for r in self.__spec.get_stateless_rules():
            self.__matched.append(ns(rule=r, rtme=self))

    @argres(show_result=False)
    def __copy_matched_rules(self, rtme):
        self.__matched = []
        for rule_rtme in rtme.__matched:
            self.__matched.append(
                ns(
                    rule=rule_rtme.rule.new_copy(),
                    rtme=self if id(rule_rtme) == id(rtme) else self.__owner[rule_rtme.rtme.get_offset()] if rule_rtme.rtme.get_offset() < self.get_offset() else rule_rtme.rtme.get_offset()
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
            if isinstance(rule_rtme.rtme, (RtMatchEntry, RtVirtualEntry)):
                continue
            # FIXME For or subseq calls except subseq(0. -2) when last entry
            # is tmp we will get outofrange exception
            rule_rtme.rtme = self.__owner[rule_rtme.rtme]
        return True

    @argres(show_result=False)
    def __index_rules(self):
        self.__required_count = 0
        for r in self.__pending:
            if not r.is_optional():
                self.__required_count += 1

    def __create_name(self, name):
        self.__name = RtMatchString(name)
        if self.__name.need_reindex():
            self.__reindex_name(self.__name)

    def __reindex_name(self, name):
        stack = self.__owner.get_stack()
        if name.get_max_level() is not None:
            stack = stack[0:max(name.get_max_level() - 1, 0)]
        try:
            name.update(str(name).format(*stack))
        except IndexError:
            stack = stack + ['\\d+'] * 20
            str_name = str(name).replace('[', '\\[').replace(']', '\\]').replace('+', '\\+')
            name.update(str_name.format(*stack))

    @argres()
    def __decrease_rule_counters(self, rule):
        if not rule.is_persistent():
            self.__required_count -= 1
        return self.__required_count

    def get_name(self):
        return self.__name

    def get_owner(self):
        return self.__owner

    def get_form(self):
        return self.__form

    def get_spec(self):
        return self.__spec

    def get_offset(self, base=None):
        return self.__rtms_offset

    def get_reliability(self):
        return self.__reliability

    @argres()
    def has_pending(self, required_only=False):
        if required_only:
            return self.__required_count > 0
        return len(self.__pending) > 0

    @argres(show_result=False)
    def add_link(self, link):
        self.__owner.add_link(link)

    @argres()
    def find_transitions(self, forms):
        return reduce(
            lambda x, y: x + y,
            map(
                lambda form:
                    filter(
                        lambda (frm, trs): trs.get_to().is_static_applicable(frm),
                        map(
                            lambda trs: (form, trs),
                            self.__spec.get_transitions(filt_fcn=lambda t: not t.get_to().is_fini())
                        )
                    ),
                forms.get_forms()
            )
        ) + map(
            lambda trs: (parser.lang.common.SpecStateFiniForm(), trs),
            self.__spec.get_transitions(filt_fcn=lambda t: t.get_to().is_fini())
        )

    @argres()
    def handle_rules(self, on_entry=None):
        pending = []
        entries = [on_entry, ] if on_entry is not None else self.__owner.get_entries(hidden=True, exclude=self)
        for r in self.__pending:
            applied = False
            for e in entries:
                if self.__check_applicable(r, e):
                    applied = True
                    if not self.__apply_on(r, e):
                        return False
                    self.__decrease_rule_counters(r)
                    self.__add_matched_rule(r, e)
                    if not r.is_persistent():
                        break
            if not applied or r.is_persistent():
                pending.append(r)
            self.__pending = pending
        return True

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
        return self.__attributes.has_key(name)

    def get_attribute(self, name):
        return self.__attributes[name]

    def __repr__(self):
        try:
            return "RtMatchEntry(objid={0}, name='{1}')".format(hex(id(self)), self.get_name())
        except:
            return "RtMatchEntry(objid={0})".format(hex(id(self)))

    def __str__(self):
        try:
            return "RtMatchEntry(objid={0}, name='{1}')".format(hex(id(self)), self.get_name())
        except:
            return "RtMatchEntry(objid={0})".format(hex(id(self)))


class RtTmpEntry(object):
    def __new__(cls, *args, **kwargs):
        obj = super(RtTmpEntry, cls).__new__(cls)
        owner = args[0]
        obj.logger = owner.get_logger() if owner is not None else None
        return obj

    def get_logger(self):
        return self.logger

    @argres(show_result=False)
    def __init__(self, owner, based_on):
        assert isinstance(based_on, ns)
        self.__init_from_form_spec(owner, based_on.form, based_on.spec_state_def, based_on.rtms_offset)

    @argres(show_result=False)
    def __init_from_form_spec(self, owner, form, spec_state_def, rtms_offset):
        assert form is not None and spec_state_def is not None
        self.__owner = owner
        self.__form = form
        self.__spec = spec_state_def
        self.__rtms_offset = rtms_offset
        self.__reliability = spec_state_def.get_reliability() * form.get_reliability()
        self.__sub_ctx = None

        self.__create_name(self.__spec.get_name())

    def get_matched_rules(self):
        return []

    def get_subctx(self):
        return self.__sub_ctx

    @argres(show_result=True)
    def matched_list_valid(self):
        for rule_rtme in self.__matched:
            if isinstance(rule_rtme.rtme, RtMatchEntry):
                continue
            return False
        return True

    @argres(show_result=False)
    def resolve_matched_rtmes(self):
        return True

    def __create_name(self, name):
        self.__name = RtMatchString(name)
        if self.__name.need_reindex():
            self.__reindex_name(self.__name)

    def __reindex_name(self, name):
        stack = self.__owner.get_stack()
        if name.get_max_level() is not None:
            stack = stack[0:max(name.get_max_level() - 1, 0)]
        try:
            name.update(str(name).format(*stack))
        except IndexError:
            stack = stack + ['\\d+'] * 20
            str_name = str(name).replace('[', '\\[').replace(']', '\\]').replace('+', '\\+')
            name.update(str_name.format(*stack))

    def get_name(self):
        return self.__name

    def get_owner(self):
        return self.__owner

    def get_form(self):
        return self.__form

    def get_spec(self):
        return self.__spec

    def get_offset(self, base=None):
        return self.__rtms_offset

    def get_reliability(self):
        return self.__reliability

    @argres()
    def has_pending(self, required_only=False):
        if required_only:
            return self.__required_count > 0
        return len(self.__pending) > 0

    @argres(show_result=False)
    def add_link(self, link):
        self.__owner.add_link(link)

    @argres()
    def find_transitions(self, forms):
        return map(
            lambda f: (f, TrsDef(None, self.get_spec(), st_to=self.get_spec())),
            forms.get_forms()
        )

    @argres()
    def handle_rules(self, on_entry=None):
        return True

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
        rtms = self.__owner.subseq(start=0, stop=-2)
        subseq_anchor = res.sq.get_anchors()[0].get_form()
        rtme = RtMatchEntry(
            rtms,
            ns(
                form=subseq_anchor,
                spec_state_def=self.__spec,
                rtms_offset=self.__rtms_offset,
                attributes={
                    'subseq': MatchedSequence(res.sq)
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
            new_rtms = RtMatchSequence(rtms)
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

    def __repr__(self):
        try:
            return "RtTmpEntry(objid={0}, name='{1}')".format(hex(id(self)), self.get_name())
        except:
            return "RtTmpEntry(objid={0})".format(hex(id(self)))

    def __str__(self):
        try:
            return "RtTmpEntry(objid={0}, name='{1}')".format(hex(id(self)), self.get_name())
        except:
            return "RtTmpEntry(objid={0})".format(hex(id(self)))


class RtVirtualEntry(object):
    def __new__(cls, *args, **kwargs):
        obj = super(RtVirtualEntry, cls).__new__(cls)
        owner = args[0]
        obj.logger = owner.get_logger() if owner is not None else None
        return obj

    def get_logger(self):
        return self.logger

    @argres(show_result=False)
    def __init__(self, owner, based_on):
        if isinstance(based_on, RtVirtualEntry):
            self.__init_from_rtme(owner, based_on)
        else:
            self.__init_from_form_spec(
                owner,
                based_on.form,
                based_on.spec_state_def,
                based_on.rtms_offset,
                based_on.attributes if hasattr(based_on, 'attributes') else {}
            )

    @argres(show_result=False)
    def __init_from_form_spec(self, owner, form, spec_state_def, rtms_offset, attributes):
        assert form is not None and spec_state_def is not None
        self.__owner = owner
        self.__form = parser.lang.common.SpecStateVirtForm(self)
        self.__spec = spec_state_def
        self.__rtms_offset = rtms_offset
        self.__reliability = spec_state_def.get_reliability() * form.get_reliability()
        self.__attributes = attributes
        self.__referers = []
        self.__uniq = None
        self.__aggregated_info = None

        self.__create_name(self.__spec.get_name())
        self.__create_rules()
        self.__index_rules()
        self.__create_static_rules()

    @argres(show_result=False)
    def __init_from_rtme(self, owner, rtme):
        self.__owner = owner
        self.__form = parser.lang.common.SpecStateVirtForm(self)
        self.__spec = rtme.__spec
        self.__rtms_offset = rtme.__rtms_offset
        self.__reliability = rtme.__reliability
        self.__referers = []
        self.__uniq = rtme.get_aggregated_uniq()
        self.__aggregated_info = copy.deepcopy(rtme.get_aggregated_info())

        self.__name = RtMatchString(rtme.__name)
        self.__pending = rtme.__pending[:]
        self.__copy_attributes(rtme)
        self.__index_rules()
        self.__copy_matched_rules(rtme)
        self.__copy_referers(rtme)

    @argres(show_result=False)
    def __copy_attributes(self, rtme):
        self.__attributes = {k: v for k, v in rtme.__attributes.items()}

    @argres(show_result=False)
    def __create_rules(self):
        self.__pending = []
        for r in self.__spec.get_rt_rules():
            assert r is not None
            for b in r.get_bindings():
                if b.need_reindex():
                    self.__reindex_name(b)
            self.__pending.append(r)

    @argres(show_result=False)
    def __create_static_rules(self):
        self.__matched = []
        for r in self.__spec.get_stateless_rules():
            self.__matched.append(ns(rule=r, rtme=self))

    @argres(show_result=False)
    def __copy_matched_rules(self, rtme):
        self.__matched = []
        for rule_rtme in rtme.__matched:
            self.__matched.append(
                ns(
                    rule=rule_rtme.rule.new_copy(),
                    rtme=self if id(rule_rtme) == id(rtme) else self.__owner[rule_rtme.rtme.get_offset()] if rule_rtme.rtme.get_offset() < self.get_offset() else rule_rtme.rtme.get_offset()
                )
            )

    @argres(show_result=False)
    def __copy_referers(self, rtme):
        self.__referers = []
        for referer in rtme.__referers:
            self.__referers.append(
                self.__owner[referer.get_offset()] if referer.get_offset() < self.get_offset() else referer.get_offset()
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
            if isinstance(rule_rtme.rtme, (RtMatchEntry, RtVirtualEntry)):
                continue
            # FIXME For or subseq calls except subseq(0. -2) when last entry
            # is tmp we will get outofrange exception
            rule_rtme.rtme = self.__owner[rule_rtme.rtme]

        for i, referer in enumerate(self.__referers):
            if isinstance(referer, (RtMatchEntry, RtVirtualEntry)):
                continue
            self.__referers[i] = self.__owner[self.__referers[i]]

        return True

    @argres(show_result=False)
    def __index_rules(self):
        self.__required_count = 0
        for r in self.__pending:
            if not r.is_optional():
                self.__required_count += 1

    def __create_name(self, name):
        self.__name = RtMatchString(name)
        if self.__name.need_reindex():
            self.__reindex_name(self.__name)

    def __reindex_name(self, name):
        stack = self.__owner.get_stack()
        if name.get_max_level() is not None:
            stack = stack[0:max(name.get_max_level() - 1, 0)]
        try:
            name.update(str(name).format(*stack))
        except IndexError:
            stack = stack + ['\\d+'] * 20
            str_name = str(name).replace('[', '\\[').replace(']', '\\]').replace('+', '\\+')
            name.update(str_name.format(*stack))

    @argres()
    def __decrease_rule_counters(self, rule):
        if not rule.is_persistent():
            self.__required_count -= 1
        return self.__required_count

    def get_name(self):
        return self.__name

    def get_owner(self):
        return self.__owner

    def get_form(self):
        return self.__form

    def get_spec(self):
        return self.__spec

    def get_offset(self, base=None):
        return self.__rtms_offset

    def get_reliability(self):
        return self.__reliability

    def get_aggregated_uniq(self):
        if self.__uniq is None:
            self.__recalculate_aggregated_props()
        return self.__uniq

    def get_aggregated_info(self):
        if self.__aggregated_info is None or not self.__aggregated_info:
            self.__recalculate_aggregated_props()
        return self.__aggregated_info

    @argres()
    def has_pending(self, required_only=False):
        if required_only:
            return self.__required_count > 0
        return len(self.__pending) > 0

    @argres(show_result=False)
    def add_link(self, link):
        self.__owner.add_link(link)

    @argres()
    def find_transitions(self, forms):
        return reduce(
            lambda x, y: x + y,
            map(
                lambda form:
                    filter(
                        lambda (frm, trs): trs.get_to().is_static_applicable(frm),
                        map(
                            lambda trs: (form, trs),
                            self.__spec.get_transitions(filt_fcn=lambda t: not t.get_to().is_fini())
                        )
                    ),
                forms.get_forms()
            )
        ) + map(
            lambda trs: (parser.lang.common.SpecStateFiniForm(), trs),
            self.__spec.get_transitions(filt_fcn=lambda t: t.get_to().is_fini())
        )

    @argres()
    def handle_rules(self, on_entry=None):
        pending = []
        entries = [on_entry, ] if on_entry is not None else self.__owner.get_entries(hidden=True, exclude=self)
        for r in self.__pending:
            applied = False
            for e in entries:
                if self.__check_applicable(r, e):
                    applied = True
                    if not self.__apply_on(r, e):
                        return False
                    self.__decrease_rule_counters(r)
                    self.__add_matched_rule(r, e)
                    if not r.is_persistent():
                        break
            if not applied or r.is_persistent():
                pending.append(r)
            self.__pending = pending
        return True

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
        return False

    def get_attribute(self, name):
        return None

    @argres()
    def attach_referer(self, rtme):
        self.__referers.append(rtme)
        self.__uniq = None
        self.__aggregated_info = None
        return True

    @argres(show_result=False)
    def __recalculate_aggregated_props(self):
        referers_uuids = '.'.join(
            sorted([r.get_form().get_uniq() for r in self.__referers])
        )
        self.__uniq = str(uuid.uuid3(uuid.NAMESPACE_DNS, referers_uuids))

        self.__aggregated_info = reduce(
            lambda x, y: self.__merge_props(x, y),
            map(
                lambda r: r.get_form().get_info(),
                self.__referers[1:]
            ),
            self.__referers[0].get_form().get_info()
        ) if self.__referers else {}

    def __merge_count(self, x, y):
        return 'plural'

    def __merge_case(self, x, y):
        if x == y:
            return x
        return None

    def __merge_gender(self, x, y):
        if x == y:
            return x
        return None

    @argres()
    def __merge_props(self, x, y):
        merge_fcn = {
            'count': self.__merge_count,
            'case': self.__merge_case,
            'gender': self.__merge_gender,
        }
        res = {}
        for k in merge_fcn.keys():
            if x.has_key(k) and y.has_key(k):
                r = merge_fcn[k](x[k], y[k])
                if r is not None:
                    res[k] = r
        return res

    def __repr__(self):
        try:
            return "RtVirtualEntry(objid={0}, name='{1}')".format(hex(id(self)), self.get_name())
        except:
            return "RtVirtualEntry(objid={0})".format(hex(id(self)))

    def __str__(self):
        try:
            return "RtVirtualEntry(objid={0}, name='{1}')".format(hex(id(self)), self.get_name())
        except:
            return "RtVirtualEntry(objid={0})".format(hex(id(self)))
