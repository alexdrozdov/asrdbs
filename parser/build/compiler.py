#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import copy
import re
import parser.spare.rules
import parser.spare.wordform
import parser.build.preprocessor
from parser.spare.rules import RtMatchString
from parser.build.objects import SpecStateDef, CompiledSpec


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


class IterableSequenceSpec(parser.spare.rules.SequenceSpec):
    def __init__(self, spec):
        super().__init__(self, spec.get_name())
        spec = copy.deepcopy(spec)
        self.__unroll_repeatable_entries(spec.get_spec())
        self.__index_all_entries()
        self.__index_layers()
        self.__index_hierarchy()
        self.__validate = spec.get_validate()

    def get_validate(self):
        return self.__validate

    def __index_subentries(self, item, level):
        if "entries" in item:
            for st in item["entries"]:
                self.__set_state_uid(st)
                self.__set_state_level(st, level)
                self.__all_entries.append(st)
                if "entries" in st or "uniq-items" in st:
                    self.__index_subentries(st, level + 1)
        if "uniq-items" in item:
            for st in item["uniq-items"]:
                self.__set_state_uid(st)
                self.__set_state_level(st, level)
                self.__all_entries.append(st)
                if "entries" in st or "uniq-items" in st:
                    self.__index_subentries(st, level + 1)

    def __index_all_entries(self):
        self.__all_entries = []
        level = 0
        for st in self.__basic_spec:
            self.__set_state_uid(st)
            self.__set_state_level(st, level)
            self.__all_entries.append(st)
            if "entries" in st or "uniq-items" in st:
                self.__index_subentries(st, level + 1)

    def __create_entry_copy(self, entry, order, set_order=False, repeatable=False, required=False):
        entry = copy.deepcopy(entry)
        if set_order:
            entry["id"] += "[{0}]".format(order)
        entry["repeatable"] = repeatable
        entry["required"] = required
        if "entries" in entry:
            entries = []
            for st in entry["entries"]:
                sub_specs = self.__unroll_entry(st)
                entries.extend(sub_specs)
            entry["entries"] = entries
        if "uniq-items" in entry:
            entries = []
            for st in entry["uniq-items"]:
                sub_specs = self.__unroll_entry(st)
                entries.extend(sub_specs)
            entry["uniq-items"] = entries
        return entry

    def __unroll_entry(self, entry):
        if "repeatable" not in entry or not isinstance(entry["repeatable"], tuple):
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
            if "entries" in st:
                self.__index_layer(st["entries"], layer=layer+1)
            if "uniq-items" in st:
                self.__index_layer(st["uniq-items"], layer=layer+1)

    def __index_layers(self):
        self.__layers = []
        self.__index_layer(self.__basic_spec)

    def __set_state_uid(self, state):
        if "uid" in state:
            return
        state["uid"] = str(uuid.uuid1())

    def __set_state_level(self, state, level):
        state["level"] = level

    def __add_child_to_parent(self, child, parent):
        self.__parents[child["uid"]] = parent

    def __index_item_entries(self, item):
        l = []
        if "entries" in item:
            for st in item["entries"]:
                l.append(st)
                self.__add_child_to_parent(st, item)
                self.__index_item_entries(st)
        if "uniq-items" in item:
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
        if item["uid"] in self.__parents:
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
        self.__local_spec_tags = {}
        self.__name_remap = {}

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
        if '$TAG' in name:
            m = re.search('\$TAG\((.+?)\)', name)
            assert m, 'wrong $TAG placeholder for spec {0}'.format(self.__spec_name)
            tag = m.group(1)
            assert tag in self.__local_spec_tags, 'tag {0} not defined for spec {1}'.format(tag, self.__spec_name)
            return len(self.__local_spec_tags[tag])
        return 1

    def __resolve_name_level(self, ref_state, name):
        return name.replace('$LEVEL', str(ref_state['level']))

    def __resolve_name_glevel(self, ref_state, name):
        return name.replace('$GLEVEL', str(ref_state['level'] + self.__level))

    def __resolve_name_lsa(self, ref_state, name, var_num):
            assert self.__local_spec_anchors, 'Tried to resolve name for spec "{0}" without local spec anchor'.format(
                self.__spec_name
            )
            assert len(self.__local_spec_anchors) == 1 or var_num is not None, 'Tried to resolve name for spec "{0}" with multiple local spec anchors {1}'.format(
                self.__spec_name,
                self.__local_spec_anchors
            )

            if var_num is None:
                anchor_name = str(self.__local_spec_anchors[0].get_name())
            else:
                anchor_name = str(self.__local_spec_anchors[var_num].get_name())
            name = name.replace('$LOCAL_SPEC_ANCHOR', anchor_name)

            return name

    def __resolve_name_tag(self, ref_state, name, var_num):
            m = re.search('\$TAG\((.+?)\)', name)
            assert m, 'wrong $TAG placeholder for spec {0}'.format(self.__spec_name)
            tag = m.group(1)

            assert tag in self.__local_spec_tags, 'Tried to resolve tag {0} for spec "{1}" without such tag'.format(
                tag,
                self.__spec_name
            )
            assert len(self.__local_spec_tags[tag]) == 1 or var_num is not None, 'Tried to resolve name for spec "{0}" with multiple tags {1}: {2}'.format(
                self.__spec_name,
                tag,
                self.__local_spec_tags[tag]
            )

            if var_num is None:
                tag_value = str(self.__local_spec_tags[tag][0].get_name())
            else:
                tag_value = str(self.__local_spec_tags[tag][var_num].get_name())
            name = re.sub('\$TAG\((.+?)\)', tag_value, name)

            return name

    def resolve_name(self, ref_state, name, var_num=None):
        if '$LEVEL' in name:
            name = self.__resolve_name_level(ref_state, name)
        if '$GLEVEL' in name:
            name = self.__resolve_name_glevel(ref_state, name)
        if '$LOCAL_SPEC_ANCHOR' in name:
            name = self.__resolve_name_lsa(ref_state, name, var_num)
        if '$TAG' in name:
            name = self.__resolve_name_tag(ref_state, name, var_num)
        if '$INCAPSULATED' in name:
            assert 'include' in ref_state and len(ref_state['include']) == 1
            name = name.replace('$INCAPSULATED', ref_state['include'][0])
        if '$THIS' in name:
            assert '$THIS' not in ref_state['id'], 'Recursive name with $THIS spec'
            this_path = self.gen_state_name(ref_state)
            name = name.replace('$THIS', this_path)
        if '$PARENT' in name:
            assert name.find('$PARENT') == 0, '$PARENT must be first'
            parent_path = self.__create_parent_path(ref_state)
#             original_name = name
            name = name.replace('$PARENT', parent_path)
#            print(ref_state, original_name, ' -> ', name)
        elif '$SPEC' in name:
            assert name.find('$SPEC') == 0, '$SPEC must be first'
            spec_path = self.__create_spec_path()
            name = name.replace('$SPEC', spec_path)
        elif name.find('::') != 0:
            print("Compile warning: $-definition is missing for", self.__spec_name, name)
        return name

    def __add_name_remap(self, original, target):
        original = str(original)
        targets = []
        if original in self.__name_remap:
            targets = self.__name_remap[original]
        if not isinstance(target, list):
            target = [target, ]
        target = [str(t) for t in target]
        targets.extend(target)
        self.__name_remap[original] = list(set(targets))

    def __copy_name_remap(self, compiled_spec):
        for k, v in list(compiled_spec.get_name_remap().items()):
            self.__add_name_remap(k, v)

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

    def __add_include_remap(self, state):
        if state.includes_spec():
            in_spec = state.get_included()
            in_spec_anchors = in_spec.get_local_spec_anchors()
            if in_spec_anchors:
                for a in in_spec_anchors:
                    self.__add_name_remap(state.get_name(), a)

    def __get_tag_entries_list(self, tag_name):
        if tag_name not in self.__local_spec_tags:
            self.__local_spec_tags[tag_name] = []
        return self.__local_spec_tags[tag_name]

    def __handle_tag_state(self, state):
        if state.is_container() or state.is_uniq_container():
            return

        tag_name = state.get_tag()
        if state.includes_spec():
            in_spec = state.get_included()
            in_spec_anchors = in_spec.get_local_spec_anchors()
            if in_spec_anchors:
                self.__get_tag_entries_list(tag_name).extend(in_spec_anchors)
            return

        self.__get_tag_entries_list(tag_name).append(state)

    def __handle_include_state(self, state):
        in_spec_name = state.get_include_name()
        in_spec = self.__owner.get_spec(in_spec_name)
        if self.__spec_depth <= 1 or state.include_is_static_only():
            compiler = SpecCompiler(
                owner=self.__owner,
                stack=self.__stack,
                level=state.get_glevel() + 1,
                reliability=state.get_reliability()
            )
            compiled_in_spec = compiler.compile(
                in_spec,
                parent_spec_name=str(state.get_name())
            )
            state.set_incapsulated_spec(compiled_in_spec)
        else:
            state.set_dynamic()

    def __create_state(self, spec, st):
        state_name = self.gen_state_name(st)
        state = SpecStateDef(self, state_name, st)
        if state.get_level() > 0:
            parent_st = spec.get_parent(st)
            parent_state_name = str(self.gen_state_name(parent_st))
            parent_state = self.__name2state[parent_state_name]
            state.set_parent_state(parent_state)
            if parent_state.is_anchor():
                state.force_anchor()
            if parent_state.is_tagged():
                state.force_tag(parent_state.get_tag())
            state.inherit_reliability(parent_state.get_reliability())
            self.__add_name_remap(parent_state_name, state_name)
        else:
            state.inherit_reliability(self.get_reliability())

        if state.has_include():
            self.__handle_include_state(state)

        if state.is_anchor():
            self.__handle_anchor_state(state)

        if state.is_tagged():
            self.__handle_tag_state(state)

        self.__add_include_remap(state)
        self.__add_state(state)

    def __create_states(self, spec):
        spec_iter = spec.get_state_iter()
        for st in spec_iter.get_all_entries():
            self.__create_state(spec, st)

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

    def __propagate_container_rules(self, spec):
        deepest = spec.get_level_count()

        for level in range(deepest):
            spec_iter = spec.get_level_iter(level)
            for st in spec_iter.get_all_entries():
                state = self.__name2state[str(self.gen_state_name(st))]
                if not state.is_container() and not state.is_uniq_container():
                    continue
                if not state.has_rules():
                    continue
                self.__propagate_rules_to_childs(spec, state)

    def __propagate_rules_to_childs(self, spec, state):
        rules_to_incapsulate = state.get_rules_list()

        spec_iter = spec.get_hierarchical_iter(state.get_spec())
        for s in spec_iter.get_all_entries():
            c_state = self.__name2state[str(self.gen_state_name(s))]
            c_state.extend_rules(
                copy.deepcopy(rules_to_incapsulate),
                state.get_glevel(),
                original_state=state
            )

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
            self.__copy_name_remap(compiled_in_spec)
            self.__states.remove(state)

    def __review_anchors(self):
        for state in self.__states:
            if not state.is_anchor():
                continue
            if state not in self.__local_spec_anchors:
                state.force_anchor(is_anchor=False)

    def __review_tags(self):
        for state in self.__states:
            if not state.is_tagged():
                continue
            tagged_states = self.__get_tag_entries_list(state.get_tag())
            if state not in tagged_states:
                state.force_tag(None)

    def __aggregate_entrance_rules(self):
        ini = self.__states[0]

        aggregated_rule = parser.spare.rules.RuleOr()
        for st in ini.get_accessable(virtual=True, follow_virtual=False):
            aggregated_rule += parser.spare.rules.RuleAnd(st.get_stateless_rules())
        ini.set_stateless_rules([aggregated_rule, ])

    def __aggregate_virtual_entries_rules(self):
        for state in self.__states:
            if not state.is_virtual():
                continue
            self.__aggregate_virtual_entry_rules(state)

    def __aggregate_virtual_entry_rules(self, state):
        aggregated_rule = parser.spare.rules.RuleOr()
        for st in state.get_accessable(virtual=False, follow_virtual=True):
            aggregated_rule += parser.spare.rules.RuleAnd(st.get_stateless_rules())
        state.set_stateless_rules([aggregated_rule, ])

    def register_rule_binding(self, rule, binding):
        return

    def binding_needs_resolve(self, binding):
        assert isinstance(binding, RtMatchString)
        if str(binding) in self.__name2state:
            state = self.__name2state[str(binding)]
            if not state.is_container() and not state.is_uniq_container() and not state.includes_spec():
                return False
            return True
        if str(binding) in self.__name_remap:
            return True
        print(self.__parent_spec_name)
        print(binding)
        print(list(self.__name2state.keys()))
        print(list(self.__name_remap.keys()))
        raise RuntimeError('state name matching not implemented')

    def resolve_binding(self, binding):
        assert isinstance(binding, RtMatchString)
        if str(binding) in self.__name2state:
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
        print(binding)
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
        self.__propagate_container_rules(spec)
        self.__remove_containers()
        self.__merge_transitions()
        self.__incapsulate_rules()
        self.__incapsulate_states()
        self.__create_state_rules()
        self.__review_anchors()
        self.__review_tags()
        self.__aggregate_virtual_entries_rules()
        self.__aggregate_entrance_rules()

        cs = CompiledSpec(
            spec,
            self.__spec_name,
            self.__states,
            self.__inis,
            self.__finis,
            self.__local_spec_anchors,
            self.__name_remap,
            spec.get_validate() if self.__level == 0 else None
        )
        self.__stack.pop()
        return cs

    def get_level(self):
        return self.__level

    def get_reliability(self):
        return self.__reliability
