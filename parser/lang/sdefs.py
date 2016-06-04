#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import RtStaticRule, SelectorRuleFactory


class c__pos_check(RtStaticRule):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def new_copy(self):
        return c__pos_check(self.__pos_names)

    def match(self, form):
        return form.get_pos() in self.__pos_names

    def get_info(self, wrap=False):
        return u'pos: {0}'.format(self.__pos_names[0])


class c__placeholder(RtStaticRule):
    def __init__(self, def_value):
        self.__def_value = def_value

    def new_copy(self):
        return c__placeholder(self.__def_value)

    def match(self, form):
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
