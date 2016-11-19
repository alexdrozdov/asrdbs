#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import parser.matcher
import parser.spare.rules
import parser.spare.wordform
import parser.build.preprocessor
import parser.lang.base.rules.defs
from parser.spare.rules import RtMatchString


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
            self.__levelpath = list(range(self.__from.get_glevel() + 1, self.__to.get_glevel() + 1))
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
            self.__levelpath = list(range(self.__from.get_glevel() + 1, upper_level + 1))

        if upper_level < trs_to.get_from().get_glevel():
            self.__levelpath.extend(list(range(upper_level + 1, trs_to.get_from().get_glevel())))

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

    static_rules = ['pos_type', 'case', 'selector']
    dynamic_rules = ['same-as', 'position', 'master-slave', 'unwanted-links', 'refers-to', 'dependency-of', 'action', 'closed-with']
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
        self.__is_container = "entries" in spec_dict
        self.__is_uniq_container = "uniq-items" in spec_dict
        self.__is_contained = False
        if self.__parent:
            self.__is_contained = True
        self.__is_required = "required" in spec_dict and spec_dict["required"]
        self.__is_repeatable = "repeatable" in spec_dict and spec_dict["repeatable"]
        self.__is_local_final = False
        self.__is_init = "fsm" in spec_dict and spec_dict["fsm"] == parser.lang.base.rules.defs.FsmSpecs.init
        self.__is_fini = "fsm" in spec_dict and spec_dict["fsm"] == parser.lang.base.rules.defs.FsmSpecs.fini
        self.__is_virtual = "virtual" in spec_dict and spec_dict["virtual"]
        self.__uid = str(uuid.uuid1())
        if 'include' in spec_dict:
            self.__incapsulate_spec_name = spec_dict['include']['spec']
            self.__static_only_include = spec_dict['include']['static-only'] if 'static-only' in spec_dict['include'] else False
        else:
            self.__incapsulate_spec_name = None
            self.__static_only_include = False
        self.__incapsulate_spec = None
        self.__stateless_rules = []
        self.__rt_rules = []
        self.__level = spec_dict['level']
        self.__glevel = compiler.get_level() + self.__level
        if 'anchor' in spec_dict and isinstance(spec_dict['anchor'], list):
            spec_dict['anchor'] = spec_dict['anchor'][0]
        self.__is_local_anchor = 'anchor' in spec_dict and spec_dict['anchor'][1] in [
            parser.lang.base.rules.defs.AnchorSpecs.local_spec_anchor,
            parser.lang.base.rules.defs.AnchorSpecs.global_anchor
        ]
        if 'anchor' in spec_dict and spec_dict['anchor'][1] == parser.lang.base.rules.defs.AnchorSpecs.local_spec_tag:
            self.__tag = spec_dict['anchor'][2]
        else:
            self.__tag = None
        self.__transitions_merged = False
        self.__add_to_seq = spec_dict['add-to-seq'] if 'add-to-seq' in spec_dict else True
        self.__reliability = spec_dict['reliability'] if 'reliability' in spec_dict else 1.0
        self.__merges_with = set(spec_dict['merges-with']) if 'merges-with' in spec_dict else set()
        self.__closed = spec_dict['closed'] if 'closed' in spec_dict else True
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

    def is_tagged(self):
        return self.__tag is not None

    def is_closed(self):
        return self.__closed

    def get_tag(self):
        return self.__tag

    def fixed(self):
        return self.__fixed

    def force_anchor(self, is_anchor=True):
        self.__is_local_anchor = is_anchor

    def force_tag(self, tag_name):
        self.__tag = tag_name

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
            if r in self.__spec_dict:
                rule_def = self.__spec_dict[r]
                if isinstance(rule_def, list):
                    for rd in rule_def:
                        # print(rd, self.__name)
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
            if r in self.__spec_dict:
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
        return list(filter(
            filt_fcn,
            self.__transitions
        ))

    def get_rtransitions(self):
        return self.__rtransitions[:]

    def is_static_applicable(self, form):
        for r in self.__stateless_rules:
            if not r.match(form):
                return False
        return True

    def extend_rules(self, rules, max_level, original_state=None):
        for r, rule_def in list(rules.items()):
            if not isinstance(rule_def, list):
                rule_def = [rule_def, ]
            rule_def = [parser.spare.rules.RtRuleFactory(
                rr,
                max_level=max_level,
                original_state=original_state
            ) for rr in rule_def]
            for rr in rule_def:
                assert not rr.created()
            if r not in self.__spec_dict:
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
        return len(set(SpecStateDef.all_rules).intersection(list(self.__spec_dict.keys()))) > 0

    def has_rt_rules(self):
        return len(set(SpecStateDef.dynamic_rules).intersection(list(self.__spec_dict.keys()))) > 0

    def get_rules_list(self):
        return {r: self.__spec_dict[r] for r in SpecStateDef.all_rules if r in self.__spec_dict}

    def get_rt_rules_list(self):
        return {r: self.__spec_dict[r] for r in SpecStateDef.dynamic_rules if r in self.__spec_dict}

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
    def __init__(self, src_spec, name, states, inis, finis, local_spec_anchors, name_remap, validator):
        self.__src_spec = src_spec
        self.__name = name
        assert states, 'Spec without states'
        assert inis, 'Spec without init states'
        assert local_spec_anchors, 'Tried to create CompiledSpec "{0}" without any anchor'.format(self.__name)
        self.__states = states
        self.__inis = inis
        self.__finis = finis
        self.__local_spec_anchors = local_spec_anchors
        self.__name_remap = name_remap
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

    def get_name_remap(self):
        return self.__name_remap

    def get_validate(self):
        return self.__validator
