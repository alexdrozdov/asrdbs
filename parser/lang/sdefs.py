#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import RtStaticRule, SelectorRuleFactory, MultiSelectorRuleFactory


class c__pos_check(RtStaticRule):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def new_copy(self):
        return c__pos_check(self.__pos_names)

    def match(self, *args, **kwargs):
        return args[0].get_pos() in self.__pos_names

    def get_info(self, wrap=False):
        return 'pos: {0}'.format(self.__pos_names[0])

    def format(self, fmt):
        assert fmt == 'dict'
        return {'pos': self.__pos_names}


class c__case_check(RtStaticRule):
    def __init__(self, cases):
        self.__cases = cases

    def new_copy(self):
        return c__case_check(self.__cases)

    def match(self, *args, **kwargs):
        try:
            return args[0].get_case() in self.__cases
        except:
            pass
        return False

    def get_info(self, wrap=False):
        return 'case: {0}'.format(self.__cases[0])

    def format(self, fmt):
        assert fmt == 'dict'
        return {'case': self.__cases}


class c__equal_properties_check(RtStaticRule):
    def __init__(self, indx0, indx1, props):
        self.__indx0 = indx0
        self.__indx1 = indx1
        self.__props = props

    def new_copy(self):
        return c__equal_properties_check(self.__indx0, self.__indx1,  self.__props)

    def match(self, *args, **kwargs):
        f1 = args[self.__indx0]
        f2 = args[self.__indx1]
        for p in self.__props:
            if f1.get_property(p) != f2.get_property(p):
                return False
        return True

    def get_info(self, wrap=False):
        return 'equal: {0}'.format(self.__props)

    def format(self, fmt):
        assert fmt == 'dict'
        return {'equal': self.__props}


class c__position_check(RtStaticRule):
    def __init__(self, indx0, indx1, relative_position, cb):
        self.__indx0 = indx0
        self.__indx1 = indx1
        self.__relative_position = relative_position
        self.__cb = cb

    def new_copy(self):
        return c__position_check(
            self.__indx0,
            self.__indx1,
            self.__relative_position,
            self.__cb
        )

    def match(self, *args, **kwargs):
        p1 = args[self.__indx0].get_position()
        p2 = args[self.__indx1].get_position()
        return self.__cb(p1, p2)

    def get_info(self, wrap=False):
        return 'position: {0}'.format(self.__relative_position)

    def format(self, fmt):
        assert fmt == 'dict'
        return {'position': self.__relative_position}


class c__placeholder(RtStaticRule):
    def __init__(self, def_value):
        self.__def_value = def_value

    def new_copy(self):
        return c__placeholder(self.__def_value)

    def match(self, *args, **kwargs):
        return self.__def_value

    def get_info(self, wrap=False):
        return 'placeholder: {0}'.format(self.__def_value)

    def format(self, fmt):
        assert fmt == 'dict'
        return {'placeholder': self.__def_value}


class c__word_check(RtStaticRule):
    def __init__(self, words):
        self.__words = words

    def new_copy(self):
        return c__word_check(self.__word)

    def match(self, *args, **kwargs):
        return args[0].get_word() in self.__words

    def get_info(self, wrap=False):
        return 'pos: {0}'.format(self.__words)

    def format(self, fmt):
        assert fmt == 'dict'
        return {'pos': self.__words}


class c__bind_props(RtStaticRule):
    def __init__(self, indx0, indx1):
        self.__indx0 = indx0
        self.__indx1 = indx1

    def new_copy(self):
        return c__bind_props(
            self.__indx0,
            self.__indx1
        )

    def match(self, *args, **kwargs):
        t1 = args[self.__indx0].term()
        t2 = args[self.__indx1].term()
        return t1.bind_props(t2)

    def get_info(self, wrap=False):
        return 'bind-props: {0}'.format('all')

    def format(self, fmt):
        assert fmt == 'dict'
        return {'bind-props': 'all'}


class c__enable_props(RtStaticRule):
    def __init__(self, props_group):
        self.__props_group = props_group

    def new_copy(self):
        return c__enable_props(self.__props_group)

    def match(self, *args, **kwargs):
        t = args[0].term()
        return t.enable(self.__props_group)

    def get_info(self, wrap=False):
        return 'enable-props: {0}'.format(self.__props_group)

    def format(self, fmt):
        assert fmt == 'dict'
        return {'enable-props': self.__props_group}


class PosSpecs(object):
    def IsPos(self, pos):
        if not isinstance(pos, (list, tuple)):
            pos = [pos, ]
        return SelectorRuleFactory(c__pos_check, pos)

    def IsAnimated(self):
        return SelectorRuleFactory(c__placeholder, False)

    def IsInanimated(self):
        return SelectorRuleFactory(c__placeholder, False)


class CaseSpecs(object):
    def IsCase(self, cases):
        return SelectorRuleFactory(c__case_check, cases)


class WordSpecs(object):
    def IsWord(self, words):
        return SelectorRuleFactory(c__word_check, words)


class RelationsSpecs(object):
    def EqualProps(self, other_indx, props):
        if not isinstance(props, (list, tuple)):
            props = [props, ]
        return MultiSelectorRuleFactory(
            c__equal_properties_check,
            other_indx,
            props
        )

    def Position(self, other_indx, p):
        if isinstance(p, (list, tuple)):
            p = p[0]
        cb = {
            "left": lambda s_pos, o_pos: s_pos < o_pos,
            "right": lambda s_pos, o_pos: s_pos > o_pos,
        }[p]
        return MultiSelectorRuleFactory(c__position_check, other_indx, p, cb)


class TermPropsSpecs(object):
    def Bind(self, other_indx):
        return MultiSelectorRuleFactory(
            c__bind_props,
            other_indx
        )

    def Enable(self, p):
        if isinstance(p, (list, tuple)):
            p = p[0]
        return SelectorRuleFactory(
            c__enable_props,
            p
        )
