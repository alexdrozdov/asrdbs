#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import RtStaticRule, SelectorRuleFactory


class c__pos_check(RtStaticRule):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def new_copy(self):
        return c__pos_check(self.__pos_names)

    def match(self, *args, **kwargs):
        return args[0].get_pos() in self.__pos_names

    def get_info(self, wrap=False):
        return u'pos: {0}'.format(self.__pos_names[0])


class c__equal_properties_check(RtStaticRule):
    def __init__(self, props):
        self.__props = props

    def new_copy(self):
        return c__equal_properties_check(self.__props)

    def match(self, *args, **kwargs):
        f1 = args[0]
        f2 = args[1]
        for p in self.__props:
            if f1.get_property(p) != f2.get_property(p):
                return False
        return True

    def get_info(self, wrap=False):
        return u'equal: {0}'.format(self.__props)


class c__position_check(RtStaticRule):
    def __init__(self, relative_position, cb):
        self.__relative_position = relative_position
        self.__cb = cb

    def new_copy(self):
        return c__equal_properties_check(self.__relative_position, self.__cb)

    def match(self, *args, **kwargs):
        p1 = args[0].get_position()
        p2 = args[1].get_position()
        return self.__cb(p1, p2)

    def get_info(self, wrap=False):
        return u'position: {0}'.format(self.__relative_position)


class c__placeholder(RtStaticRule):
    def __init__(self, def_value):
        self.__def_value = def_value

    def new_copy(self):
        return c__placeholder(self.__def_value)

    def match(self, *args, **kwargs):
        return self.__def_value

    def get_info(self, wrap=False):
        return u'placeholder: {0}'.format(self.__def_value)


class PosSpecs(object):
    def IsPos(self, pos):
        if not isinstance(pos, (list, tuple)):
            pos = [pos, ]
        return SelectorRuleFactory(c__pos_check, pos)

    def IsAnimated(self):
        return SelectorRuleFactory(c__placeholder, False)

    def IsInanimated(self):
        return SelectorRuleFactory(c__placeholder, False)


class RelationsSpecs(object):
    def EqualProps(self, props):
        if not isinstance(props, (list, tuple)):
            props = [props, ]
        return SelectorRuleFactory(c__equal_properties_check, props)

    def Position(self, p):
        if isinstance(p, (list, tuple)):
            p = p[0]
        cb = {
            "left": lambda s_pos, o_pos: s_pos < o_pos,
            "right": lambda s_pos, o_pos: s_pos > o_pos,
        }[p]
        return SelectorRuleFactory(c__position_check, p, cb)
