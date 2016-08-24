#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import RtStaticRule, SelectorRuleFactory, MultiSelectorRuleFactory


class SelectorStaticRule(RtStaticRule):
    def __init__(self, name, friendly, fmt_info):
        super().__init__()
        self.__name = name
        self.__friendly = friendly
        self.__fmt_info = fmt_info

    def name(self):
        return self.__name

    def friendly(self):
        return self.__friendly

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        elif fmt == 'dot-html':
            return self.__format_dot()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __format_dot(self):
        wrap = '<BR ALIGN="LEFT"/>'
        s = '{0}{1}'.format(self.name(), wrap)
        s += wrap.join(
            ['{0}: {1}'.format(str(k_v[0]), str(k_v[1])) for k_v in list(self.__fmt_info.items())]
        )
        return s

    def __format_dict(self):
        return dict(
            [
                ('rule', self.name()),
                ('friendly', self.friendly())
            ] + list(self.__fmt_info.items())
        )

    def __repr__(self):
        return "{0}(objid={1}, name='{2}')".format(
            self.friendly(),
            hex(id(self)),
            self.name()
        )

    def __str__(self):
        return "{0}(objid={1}, name='{2}')".format(
            self.friendly(),
            hex(id(self)),
            self.name()
        )


class c__pos_check(SelectorStaticRule):
    def __init__(self, pos_names):
        super().__init__(
            name='pos',
            friendly='IsPos',
            fmt_info={'pos': pos_names}
        )
        self.__pos_names = pos_names

    def match(self, *args, **kwargs):
        return args[0].get_pos() in self.__pos_names


class c__case_check(SelectorStaticRule):
    def __init__(self, cases):
        super().__init__(
            name='case',
            friendly='IsCase',
            fmt_info={'case': cases}
        )
        self.__cases = cases

    def match(self, *args, **kwargs):
        try:
            return args[0].get_case() in self.__cases
        except:
            pass
        return False


class c__equal_properties_check(SelectorStaticRule):
    def __init__(self, indx0, indx1, props):
        super().__init__(
            name='equal-properties',
            friendly='EqualProps',
            fmt_info={'equal-properties': props}
        )
        self.__indx0 = indx0
        self.__indx1 = indx1
        self.__props = props

    def match(self, *args, **kwargs):
        f1 = args[self.__indx0]
        f2 = args[self.__indx1]
        for p in self.__props:
            if f1.get_property(p) != f2.get_property(p):
                return False
        return True


class c__position_check(SelectorStaticRule):
    def __init__(self, indx0, indx1, relative_position, cb):
        super().__init__(
            name='position',
            friendly='Position',
            fmt_info={'position': relative_position}
        )
        self.__indx0 = indx0
        self.__indx1 = indx1
        self.__relative_position = relative_position
        self.__cb = cb

    def match(self, *args, **kwargs):
        p1 = args[self.__indx0].get_position()
        p2 = args[self.__indx1].get_position()
        return self.__cb(p1, p2)


class c__placeholder(SelectorStaticRule):
    def __init__(self, def_value):
        super().__init__(
            name='placeholder',
            friendly='Placeholder',
            fmt_info={'placeholder': def_value}
        )
        self.__def_value = def_value

    def match(self, *args, **kwargs):
        return self.__def_value


class c__word_check(SelectorStaticRule):
    def __init__(self, words):
        super().__init__(
            name='word',
            friendly='IsWord',
            fmt_info={'word': words}
        )
        self.__words = words

    def match(self, *args, **kwargs):
        return args[0].get_word() in self.__words


class c__bind_props(SelectorStaticRule):
    def __init__(self, indx0, indx1):
        super().__init__(
            name='bind-props',
            friendly='Bind',
            fmt_info={}
        )
        self.__indx0 = indx0
        self.__indx1 = indx1

    def match(self, *args, **kwargs):
        t1 = args[self.__indx0].term()
        t2 = args[self.__indx1].term()
        return t1.bind_props(t2)


class c__enable_props(SelectorStaticRule):
    def __init__(self, props_group):
        super().__init__(
            name='enable-props',
            friendly='Enable',
            fmt_info={'enable-props': props_group}
        )
        self.__props_group = props_group

    def match(self, *args, **kwargs):
        t = args[0].term()
        return t.enable(self.__props_group)


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
