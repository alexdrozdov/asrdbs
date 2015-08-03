#!/usr/bin/env python
# -*- #coding: utf8 -*-


class SequenceSpec(object):
    def __init__(self, name):
        self.__name = name

    def get_spec(self):
        return self.spec

    def get_name(self):
        return self.__name


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

    def EqualTo(self, count):
        return (count, count)

    def Once(self):
        return self.EqualTo(1)


class c__pos_check(object):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def match(self, form):
        return form.get_pos() in self.__pos_names


class c__pos_check_inv(object):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def match(self, form):
        return form.get_pos() not in self.__pos_names


class c__pos_syntax_check(object):
    def __init__(self, syntax_name):
        assert syntax_name in ['comma', 'dot', 'question'], 'Unsupported syntax'
        if syntax_name == 'comma':
            self.__syntax_check_cb = self.__comma_check_cb
        if syntax_name == 'dot':
            self.__syntax_check_cb = self.__dot_check_cb
        if syntax_name == 'question':
            self.__syntax_check_cb = self.__question_check_cb

    def __comma_check_cb(self, form):
        return form.is_comma()

    def __dot_check_cb(self, form):
        return form.is_dot()

    def __question_check_cb(self, form):
        return form.is_question()

    def match(self, form):
        return form.get_pos() == 'syntax' and self.__syntax_check_cb(form)


class PosSpecs(object):
    def IsNoun(self):
        return c__pos_check(["noun", ])

    def IsAdjective(self):
        return c__pos_check(["adjective", ])

    def IsAdverb(self):
        return c__pos_check(["adverb", ])

    def IsVerb(self):
        return c__pos_check(["verb", ])

    def IsSuject(self):
        return c__pos_check(["noun", "pronoun"])

    def IsComma(self):
        return c__pos_syntax_check("comma")

    def IsExcept(self, pos_names):
        return c__pos_check_inv(pos_names)


class c__case_check(object):
    def __init__(self, cases):
        self.__cases = cases

    def match(self, form):
        return form.get_case() in self.__cases


class CaseSpecs(object):
    def IsCase(self, cases):
        return c__case_check(cases)


class c__position_spec(object):
    def __init__(self, id_name):
        self.__id_name = id_name

    def new_copy(self):
        return c__position_spec(self.__id_name)

    def clone(self):
        return c__position_spec(self.__id_name)

    def is_applicable(self, rtme, other_rtme):
        if other_rtme.get_name() == self.__id_name:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return RtRule.res_matched if rtme.get_form().get_position() < other_rtme.get_form().get_position() else RtRule.res_failed

    def always_pending(self):
        return False

    def ignore_pending_state(self):
        return False


class c__position_fini(object):
    def __init__(self, id_name):
        self.__id_name = id_name

    def new_copy(self):
        return c__position_spec(self.__id_name)

    def clone(self):
        return c__position_spec(self.__id_name)

    def is_applicable(self, rtme, other_rtme):
        if other_rtme.get_name() == self.__id_name:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return rtme.get_form().get_position() == other_rtme.get_form().get_position()


class PositionSpecs(object):
    def IsBefore(self, id_name):
        return c__position_spec(id_name)

    def SequenceEnd(self, id_name='fini'):
        return c__position_fini(id_name)

    def IsBeforeIfExists(self, id_name):
        return c__position_spec(id_name)


class c__slave_master_spec(object):
    def __init__(self, id_name):
        self.__id_name = id_name

    def new_copy(self):
        return c__slave_master_spec(self.__id_name)

    def clone(self):
        return c__slave_master_spec(self.__id_name)

    def is_applicable(self, rtme, other_rtme):
        if other_rtme.get_name() == self.__id_name:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return RtRule.res_matched if other_rtme.get_form() in rtme.get_form().get_master_forms() else RtRule.res_failed

    def always_pending(self):
        return False

    def ignore_pending_state(self):
        return False


class c__slave_master_unwanted_spec(object):
    def __init__(self, id_name):
        self.__id_name = id_name

    def new_copy(self):
        return c__slave_master_unwanted_spec(self.__id_name)

    def clone(self):
        return c__slave_master_unwanted_spec(self.__id_name)

    def is_applicable(self, rtme, other_rtme):
        if other_rtme.get_name() == self.__id_name:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        slave = rtme.get_form()
        master = other_rtme.get_form()
        for m, l in slave.get_masters():
            if m != master:
                slave.add_unwanted_link(l)

        return True

    def always_pending(self):
        return True

    def ignore_pending_state(self):
        return True


class LinkSpecs(object):
    def IsSlave(self, id_name):
        return c__slave_master_spec(id_name)

    def MastersExcept(self, id_name):
        return c__slave_master_unwanted_spec(id_name)

    def AllMasters(self):
        return c__slave_master_unwanted_spec("__all_masters")


class SpecStateIniForm(object):
    def __init__(self):
        pass

    def get_word(self):
        return u'ini'

    def get_pos(self):
        return u'ini'


class SpecStateFiniForm(object):
    def __init__(self):
        pass

    def get_word(self):
        return u'fini'

    def get_pos(self):
        return u'fini'


class RtRule(object):
    res_none = 0
    res_failed = 1
    res_matched = 2
    res_continue = 3

    def __init__(self, rule, is_static):
        assert rule is not None, "Rule required"
        self.__rule = rule
        self.__is_static = is_static

    def matched(self, form):
        assert self.__is_static, "Tried to match non static rule"
        return self.__rule.match(form)

    def is_applicable(self, on, other):
        assert not self.__is_static, "Tried to check aplicibility on static rule"
        return self.__rule.is_applicable(on, other)

    def apply_on(self, on, other):
        assert not self.__is_static, "Tried to apply on static rule"
        return self.__rule.apply_on(on, other)

    def clone(self):
        return RtRule(self.__rule.clone(), self.__is_static)

    def new_copy(self):
        return RtRule(self.__rule.new_copy(), self.__is_static)

    def get_int_rule(self):
        return self.__rule

    def always_pending(self):
        return self.__rule.always_pending()

    def ignore_pending_state(self):
        return self.__rule.ignore_pending_state()
