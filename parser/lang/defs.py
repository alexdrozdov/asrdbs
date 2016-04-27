#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.matcher
from parser.matchcmn import MatchBool
from parser.lang.common import RtStaticRule, RtDynamicRule, RtMatchString, RtRuleFactory, RtRule
from argparse import Namespace as ns


class FsmSpecs(object):
    init = 1
    fini = 2

    def IsInit(self):
        return FsmSpecs.init

    def IsFini(self):
        return FsmSpecs.fini


class RequiredSpecs(object):
    def IsNecessary(self):
        return True

    def IsOptional(self):
        return False


class RepeatableSpecs(object):
    def EqualOrMoreThan(self, count):
        return (count, None)

    def LessOrEqualThan(self, count):
        return (0, count)

    def EqualTo(self, count):
        return (count, count)

    def Once(self):
        return self.EqualTo(1)

    def Any(self):
        return self.EqualOrMoreThan(0)

    def Never(self):
        return (None, None)


class AnchorSpecs(object):
    no_anchor = 0
    local_spec_anchor = 1
    local_spec_tag = 2
    global_anchor = 3

    def LocalSpecAnchor(self, name=None):
        return (True, AnchorSpecs.local_spec_anchor, name)

    def Tag(self, name):
        return (True, AnchorSpecs.local_spec_tag, name)


class c__pos_check(RtStaticRule):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def new_copy(self):
        return c__pos_check(self.__pos_names)

    def match(self, form):
        return form.get_pos() in self.__pos_names

    def get_info(self, wrap=False):
        return u'pos: {0}'.format(self.__pos_names[0])


class c__pos_check_inv(RtStaticRule):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def new_copy(self):
        return c__pos_check_inv(self.__pos_names)

    def match(self, form):
        return form.get_pos() not in self.__pos_names

    def get_info(self, wrap=False):
        return u'not pos: {0}'.format(self.__pos_names[0])


class c__pos_syntax_check(RtStaticRule):
    def __init__(self, syntax_name):
        assert syntax_name in ['comma', 'dot', 'question'], 'Unsupported syntax {0}'.format(syntax_name)
        self.__syntax = syntax_name
        if syntax_name == 'comma':
            self.__syntax_check_cb = self.__comma_check_cb
        if syntax_name == 'dot':
            self.__syntax_check_cb = self.__dot_check_cb
        if syntax_name == 'question':
            self.__syntax_check_cb = self.__question_check_cb

    def new_copy(self):
        return c__pos_syntax_check(self.__syntax)

    def __comma_check_cb(self, form):
        return form.is_comma()

    def __dot_check_cb(self, form):
        return form.is_dot()

    def __question_check_cb(self, form):
        return form.is_question()

    def match(self, form):
        return form.get_pos() == 'syntax' and self.__syntax_check_cb(form)

    def get_info(self, wrap=False):
        return u'syntax: {0}'.format(self.__syntax)


class PosSpecs(object):
    def IsNoun(self):
        return RtRuleFactory(c__pos_check, ["noun", ])

    def IsAdjective(self):
        return RtRuleFactory(c__pos_check, ["adjective", ])

    def IsAdverb(self):
        return RtRuleFactory(c__pos_check, ["adverb", ])

    def IsVerb(self):
        return RtRuleFactory(c__pos_check, ["verb", ])

    def IsUnion(self):
        return RtRuleFactory(c__pos_check, ["union", ])

    def IsPronoun(self):
        return RtRuleFactory(c__pos_check, ["pronoun", ])

    def IsPreposition(self):
        return RtRuleFactory(c__pos_check, ["preposition", ])

    def IsParticipal(self):
        return RtRuleFactory(c__pos_check, ["participal", ])

    def IsComma(self):
        return RtRuleFactory(c__pos_syntax_check, "comma")

    def IsExcept(self, pos_names):
        return RtRuleFactory(c__pos_check_inv, pos_names)


class c__word_check(RtStaticRule):
    def __init__(self, words):
        self.__words = words

    def new_copy(self):
        return c__word_check(self.__words)

    def match(self, form):
        return form.get_word() in self.__words

    def get_info(self, wrap=False):
        return u'word: {0}'.format(self.__words)


class WordSpecs(object):
    def IsWord(self, words):
        return RtRuleFactory(c__word_check, words)


class c__case_check(RtStaticRule):
    def __init__(self, cases):
        self.__cases = cases

    def new_copy(self):
        return c__case_check(self.__cases)

    def match(self, form):
        try:
            return form.get_case() in self.__cases
        except:
            pass
        return False

    def get_info(self, wrap=False):
        return u'case: {0}'.format(self.__cases[0])


class CaseSpecs(object):
    def IsCase(self, cases):
        return RtRuleFactory(c__case_check, cases)


class c__position_spec(RtDynamicRule):
    def __init__(self, anchor=None):
        RtDynamicRule.__init__(self, False, False)
        self.__anchor = RtMatchString(anchor)

    def new_copy(self):
        return c__position_spec(self.__anchor)

    def clone(self):
        return c__position_spec(self.__anchor)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return RtRule.res_matched if rtme.get_form().get_position() < other_rtme.get_form().get_position() else RtRule.res_failed

    def get_info(self, wrap=False):
        s = u'position{0}'.format('<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' id_name: {0}{1}'.format(self.__anchor, '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_persistent: {0}{1}'.format(self.is_persistent(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_optional: {0}{1}'.format(self.is_optional(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        return s

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]


class c__position_fini(RtDynamicRule):
    def __init__(self, anchor=None):
        RtDynamicRule.__init__(self, False, False)
        self.__anchor = RtMatchString(anchor)

    def new_copy(self):
        return c__position_spec(self.__anchor)

    def clone(self):
        return c__position_spec(self.__anchor)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return RtRule.res_matched if rtme.get_form().get_position() == other_rtme.get_form().get_position() else RtRule.res_failed

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]


class PositionSpecs(object):
    def IsBefore(self, anchor):
        return RtRuleFactory(c__position_spec, anchor=anchor)

    def SequenceEnd(self, anchor='fini'):
        return RtRuleFactory(c__position_fini, anchor=anchor)

    def IsBeforeIfExists(self, anchor):
        return RtRuleFactory(c__position_spec, anchor=anchor)


class c__sameas_spec(RtDynamicRule):
    def __init__(self, anchor=None, get_param_fcn=None, param_name=None):
        assert get_param_fcn is not None
        RtDynamicRule.__init__(self, False, False)
        self.__anchor = RtMatchString(anchor)
        self.__get_param_fcn = get_param_fcn
        self.__param_name = param_name

    def new_copy(self):
        return c__sameas_spec(self.__anchor, self.__get_param_fcn, self.__param_name)

    def clone(self):
        return c__sameas_spec(self.__anchor, self.__get_param_fcn, self.__param_name)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return RtRule.res_matched if self.__get_param_fcn(rtme) == self.__get_param_fcn(other_rtme) else RtRule.res_failed

    def get_info(self, wrap=False):
        s = u'same_as{0}'.format('<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' id_name: {0}{1}'.format(self.__anchor, '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' param: {0}{1}'.format(self.__param_name, '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_persistent: {0}{1}'.format(self.is_persistent(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_optional: {0}{1}'.format(self.is_optional(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        return s

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]


class SameAsSpecs(object):
    def SameCase(self, anchor):
        return RtRuleFactory(
            c__sameas_spec,
            anchor=anchor,
            get_param_fcn=lambda rtme: rtme.get_form().get_case(),
            param_name='case'
        )

    def SamePartOfSpeech(self, anchor):
        return RtRuleFactory(
            c__sameas_spec,
            anchor=anchor,
            get_param_fcn=lambda rtme: rtme.get_form().get_pos(),
            param_name='pos_type'
        )

    def SameCount(self, anchor):
        return RtRuleFactory(
            c__sameas_spec,
            anchor=anchor,
            get_param_fcn=lambda rtme: rtme.get_form().get_count(),
            param_name='count'
        )

    def SameTime(self, anchor):
        return RtRuleFactory(
            c__sameas_spec,
            anchor=anchor,
            get_param_fcn=lambda rtme: rtme.get_form().get_time(),
            param_name='time'
        )


class c__slave_master_spec(RtDynamicRule):
    def __init__(self, anchor=None, weight=None):
        RtDynamicRule.__init__(self, True, False)
        self.__anchor = RtMatchString(anchor)
        self.__weight = weight

    def new_copy(self):
        return c__slave_master_spec(self.__anchor, self.__weight)

    def clone(self):
        return c__slave_master_spec(self.__anchor, self.__weight)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        rtme_form = rtme.get_form()
        other_form = other_rtme.get_form()
        res = parser.matcher.match(other_form, rtme_form)
        if res:
            rtme.add_link(
                [
                    ns(master=other_rtme, slave=rtme, details=res.to_dict()),
                    ns(master=other_rtme, slave=rtme, details=self.to_dict()),
                ]
            )
        return RtRule.res_matched if res else RtRule.res_failed

    def get_info(self, wrap=False):
        s = u'master-slave{0}'.format('<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' id_name: {0}{1}'.format(self.__anchor, '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_persistent: {0}{1}'.format(self.is_persistent(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_optional: {0}{1}'.format(self.is_optional(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        return s

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]

    def to_dict(self):
        return {
            'rule': 'c__slave_master_spec',
            'res': MatchBool.defaultTrue,
            'reliability': self.__weight if self.__weight is not None else 1.0,
            'id_name': self.__anchor,
            'is_persistent': self.is_persistent(),
            'is_optional': self.is_optional(),
        }

    def __repr__(self):
        return "MasterSlave(objid={0}, anchor='{1}')".format(hex(id(self)), self.__anchor)

    def __str__(self):
        return "MasterSlave(objid={0}, anchor='{1}')".format(hex(id(self)), self.__anchor)


class c__slave_master_unwanted_spec(RtDynamicRule):
    def __init__(self, anchor, weight=None):
        RtDynamicRule.__init__(self, True, True)
        self.__anchor = RtMatchString(anchor)
        self.__weight = weight

    def new_copy(self):
        return c__slave_master_unwanted_spec(self.__anchor, self.__weight)

    def clone(self):
        return c__slave_master_unwanted_spec(self.__anchor, self.__weight)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return RtRule.res_matched

        slave = rtme.get_form()
        master = other_rtme.get_form()
        for m, l in slave.get_masters():
            if m != master:
                rtme.add_unwanted_link(l, weight=self.__weight, rule=self)

    def get_info(self, wrap=False):
        s = u'unwanted-links{0}'.format('<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' id_name: {0}{1}'.format(self.__anchor, '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_persistent: {0}{1}'.format(self.is_persistent(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_optional: {0}{1}'.format(self.is_optional(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        return s

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]

    def __repr__(self):
        return "UnwantedExcept(objid={0}, anchor='{1}')".format(hex(id(self)), self.__anchor)

    def __str__(self):
        return "UnwantedExcept(objid={0}, anchor='{1}')".format(hex(id(self)), self.__anchor)


class LinkSpecs(object):
    def IsSlave(self, anchor, weight=None):
        return RtRuleFactory(c__slave_master_spec, anchor=anchor, weight=weight)

    def MastersExcept(self, anchor, weight=None):
        return RtRuleFactory(c__slave_master_unwanted_spec, anchor=anchor, weight=weight)

    def AllMasters(self, weight=None):
        return RtRuleFactory(c__slave_master_unwanted_spec, ("__all_masters", ))


class c__refersto_spec(RtDynamicRule):
    def __init__(self, anchor=None):
        RtDynamicRule.__init__(self, False, False)
        self.__anchor = RtMatchString(anchor)

    def new_copy(self):
        return c__refersto_spec(self.__anchor)

    def clone(self):
        return c__refersto_spec(self.__anchor)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, aggregator_rtme):
        aggregator_rtme.attach_referer(rtme)
        rtme.add_link(
            [
                ns(master=aggregator_rtme, slave=rtme, details=self.to_dict()),
            ]
        )
        return RtRule.res_matched

    def get_info(self, wrap=False):
        s = u'refers-to{0}'.format('<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' id_name: {0}{1}'.format(self.__anchor, '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_persistent: {0}{1}'.format(self.is_persistent(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_optional: {0}{1}'.format(self.is_optional(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        return s

    def to_dict(self):
        return {
            'rule': 'c__refersto_spec',
            'res': MatchBool.defaultTrue,
            'id_name': self.__anchor,
            'is_persistent': self.is_persistent(),
            'is_optional': self.is_optional(),
        }

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]


class RefersToSpecs(object):
    def AttachTo(self, anchor):
        return RtRuleFactory(
            c__refersto_spec,
            anchor=anchor
        )


class c__dependencyof_spec(RtDynamicRule):
    def __init__(self, anchor=None, weight=None):
        RtDynamicRule.__init__(self, True, False)
        self.__anchor = RtMatchString(anchor)
        self.__weight = weight

    def new_copy(self):
        return c__dependencyof_spec(self.__anchor, self.__weight)

    def clone(self):
        return c__dependencyof_spec(self.__anchor, self.__weight)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        rtme_form = rtme.get_form()
        other_form = other_rtme.get_form()
        res = parser.matcher.match(other_form, rtme_form)
        if res:
            rtme.add_link(
                [
                    ns(master=other_rtme, slave=rtme, details=res.to_dict()),
                    ns(master=other_rtme, slave=rtme, details=self.to_dict()),
                ]
            )
        return RtRule.res_matched if res else RtRule.res_failed

    def get_info(self, wrap=False):
        s = u'dependency-of{0}'.format('<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' id_name: {0}{1}'.format(self.__anchor, '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_persistent: {0}{1}'.format(self.is_persistent(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        s += u' is_optional: {0}{1}'.format(self.is_optional(), '<BR ALIGN="LEFT"/>' if wrap else ',')
        return s

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]

    def to_dict(self):
        return {
            'rule': 'c__dependencyof_spec',
            'res': MatchBool.defaultTrue,
            'reliability': self.__weight if self.__weight is not None else 1.0,
            'id_name': self.__anchor,
            'is_persistent': self.is_persistent(),
            'is_optional': self.is_optional(),
        }

    def __repr__(self):
        return "DependencyOf(objid={0}, anchor='{1}')".format(hex(id(self)), self.__anchor)

    def __str__(self):
        return "DependencyOf(objid={0}, anchor='{1}')".format(hex(id(self)), self.__anchor)


class DependencySpecs(object):
    def DependencyOf(self, anchor, weight=None):
        return RtRuleFactory(c__dependencyof_spec, anchor=anchor, weight=weight)
