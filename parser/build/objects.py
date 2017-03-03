#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import collections
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
        self.__uid = str(uuid.uuid1())
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

    def get_uid(self):
        return self.__uid

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

    def format(self, fmt):
        if fmt != 'dict':
            raise RuntimeError('Unsupported format {0}'.format(fmt))
        return self.__format_dict()

    def __format_dict(self):
        return {
            'uuid': self.get_uid(),
            'data': {
                'from': self.get_from().get_uid(),
                'to': self.get_to().get_uid(),
                'level-path': self.__levelpath
            }
        }


class SpecStateDef(object):

    static_rules = ['pos_type', 'case', 'selector']
    dynamic_rules = ['same-as', 'position', 'master-slave', 'unwanted-links',
                     'refers-to', 'dependency-of', 'action', 'closed-with']
    all_rules = static_rules + dynamic_rules

    def __init__(self, compiler, name, spec_dict, parent=None):
        self.__uid = str(uuid.uuid1())
        self.__spec_dict = spec_dict
        self.__name = RtMatchString(name)
        self.__parent = parent
        self.__clevel = compiler.get_level()

        if self.__name.need_resolve():
            self.__name.update(
                compiler.resolve_name(spec_dict, str(self.__name))
            )

        self.__init_defaults()
        self.__init_from_spec_dict()

    def __init_defaults(self):
        self.__transitions = []
        self.__neighbour_transitions = []
        self.__child_transitions = []
        self.__rtransitions = []
        self.__is_contained = self.__parent is not None
        self.__is_local_final = False
        self.__is_local_anchor = False

        self.__incapsulate_spec_name = None
        self.__incapsulate_spec = None
        self.__static_only_include = False
        self.__dynamic_only_include = False

        self.__stateless_rules = []
        self.__rt_rules = []

        self.__transitions_merged = False

        self.__fixed = True
        self.__tags = None

    def __init_from_spec_dict(self):
        self.__is_container = self.__if_exists("entries")
        self.__is_uniq_container = self.__if_exists("uniq-items")

        self.__is_required = self.__from_spec_dict("required", False)
        self.__is_repeatable = self.__from_spec_dict("repeatable", False)

        self.__is_init = self.__from_spec_dict(
            "fsm", 0) == parser.lang.base.rules.defs.FsmSpecs.init
        self.__is_fini = self.__from_spec_dict(
            "fsm", 0) == parser.lang.base.rules.defs.FsmSpecs.fini

        self.__is_virtual = self.__from_spec_dict("virtual", False)

        self.__add_to_seq = self.__from_spec_dict('add-to-seq', True)
        self.__reliability = self.__from_spec_dict('reliability', 1.0)
        self.__merges_with = set(self.__from_spec_dict('merges-with', []))
        self.__closed = self.__from_spec_dict('closed', True)

        self.__level = self.__from_spec_dict('level', None, strict=True)
        self.__glevel = self.__clevel + self.__level

        self.__handle_include()
        self.__handle_anchor()

    def __handle_include(self):
        if not self.__if_exists('include'):
            return

        self.__incapsulate_spec_name = self.__from_spec_dict(
            'include/spec', None, strict=True)
        self.__static_only_include = self.__from_spec_dict(
            'include/static-only', False)
        self.__dynamic_only_include = self.__from_spec_dict(
            'include/dynamic-only', False)

    def __handle_anchor(self):
        anchor = self.__from_spec_dict('anchor', None)
        if anchor is None:
            return

        if not isinstance(anchor, list):
            anchor = [anchor, ]

        for a in anchor:
            if a[1] in [
                parser.lang.base.rules.defs.AnchorSpecs.local_spec_anchor,
                parser.lang.base.rules.defs.AnchorSpecs.global_anchor
            ]:
                self.__is_local_anchor = True
                continue

            if a[1] in [
                parser.lang.base.rules.defs.AnchorSpecs.local_spec_tag
            ]:
                self.append_tags([a[2], ])

    def __from_spec_dict(self, path, default, strict=False):
        sd = self.__spec_dict
        for p in (pp for pp in path.split('/') if pp):
            if p not in sd:
                if strict:
                    raise KeyError(path)
                return default
            sd = sd[p]
        return sd

    def __if_exists(self, path):
        v = self.__from_spec_dict(path, False)
        if not v:
            return v
        return True

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
        return self.__tags is not None

    def is_closed(self):
        return self.__closed

    def get_tags(self):
        return self.__tags

    def fixed(self):
        return self.__fixed

    def force_anchor(self, is_anchor=True):
        self.__is_local_anchor = is_anchor

    def append_tags(self, tags):
        if self.__tags is None:
            self.__tags = []
        self.__tags = list(set(self.__tags) | set(tags))

    def del_tag(self, tag):
        self.__tags.remove(tag)
        if not self.__tags:
            self.__tags = None

    def can_merge(self, other):
        return bool(self.__merges_with & other.__merges_with)

    def inherit_reliability(self, reliability):
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
                        if rd.created():
                            continue
                        target_list.extend(rd.create(compiler, self))
                else:
                    if not rule_def.created():
                        target_list.extend(rule_def.create(compiler, self))

    def __create_stateless_rules(self, compiler):
        self.__create_rule_list(
            compiler,
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

    def get_accessable(self, virtual=False, follow_virtual=False):
        for st in (t.get_to() for t in self.__transitions):
            if not st.is_virtual():
                yield st
            else:
                if virtual:
                    yield st
                if follow_virtual:
                    for n_st in st.get_accessable(
                        virtual=virtual,
                        follow_virtual=follow_virtual
                    ):
                        yield n_st

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

    def set_stateless_rules(self, rules):
        self.__stateless_rules = rules

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

    def static_only_include(self):
        return self.__static_only_include

    def dynamic_only_include(self):
        return self.__dynamic_only_include

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

    def format(self, fmt):
        if fmt != 'dict':
            raise RuntimeError('Unsupported format {0}'.format(fmt))
        return self.__format_dict()

    def __format_dict(self):
        attributes = [
            text_repr for is_true, text_repr in [
                (self.__is_required, 'required'),
                (self.__is_repeatable, 'repeatable'),
                (self.__is_init, 'init'),
                (self.__is_fini, 'fini'),
                (self.__is_virtual, 'virtual'),
                (self.__is_local_anchor, 'anchor'),
                (self.__is_local_final, 'local_final'),
                (self.__closed, 'closed'),
                (self.__fixed and self.__incapsulate_spec is not None, 'fixed'),
                (not self.__fixed and self.__incapsulate_spec_name, 'dynamic'),
                (not self.__add_to_seq, 'hidden'),
            ] if is_true
        ]
        data = collections.OrderedDict(
            [(k, v) for k, v in [
                ('name', str(self.__name)),
                ('uuid', self.__uid),
                ('tags', str(self.__tags) if self.__tags is not None else None),
                ('attributes', attributes),
                ('merges-with', list(self.__merges_with)),
                ('rules', {
                    'stateless': [
                        r.format('dict') for r in self.__stateless_rules],
                    'dynamic': [
                        r.format('dict') for r in self.__rt_rules],
                }),
                ('level', self.__level),
                ('glevel', self.__glevel),
                ('include', self.__incapsulate_spec_name if not self.__fixed else ""),
            ] if v is not None and (v or isinstance(v, int))
            ]
        )
        return {
            'uuid': self.get_uid(),
            'data': data
        }


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

    def get_entrance_rules(self):
        ini = self.get_inis()[0]
        return ini.get_stateless_rules()

    def format(self, fmt):
        if fmt != 'dict':
            raise RuntimeError('Unsupported format {0}'.format(fmt))
        return self.__format_dict()

    def __format_dict(self):
        nodes, links = self.__nodes_and_links()
        return {
            '__fmt_scheme': 'dg',
            '__fmt_hint': 'graph',
            '__style_hint': 'structure',
            'nodes': nodes,
            'groups': [],
            'links': links
        }

    def __nodes_and_links(self):
        nodes = []
        links = []
        for st in self.__states:
            nodes.append(st.format('dict'))
            for trs in st.get_transitions():
                nodes.append(trs.format('dict'))
                links.append({
                    'from': trs.get_from().get_uid(),
                    'to': trs.get_uid(),
                    'single2single': True
                })
                links.append({
                    'from': trs.get_uid(),
                    'to': trs.get_to().get_uid(),
                    'single2single': True
                })
        return nodes, links
