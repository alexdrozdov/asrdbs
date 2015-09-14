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

    def LessOrEqualThan(self, count):
        return (0, count)

    def EqualTo(self, count):
        return (count, count)

    def Once(self):
        return self.EqualTo(1)

    def Any(self):
        return self.EqualOrMoreThan(0)


class AnchorSpecs(object):
    no_anchor = 0
    local_spec_anchor = 1
    global_anchor = 2

    def LocalSpecAnchor(self, name=None):
        return (True, AnchorSpecs.local_spec_anchor, name)


class GroupSpecs(object):
    def LastEntry(self, group_name):
        pass


class RtRule(object):
    res_none = 0
    res_failed = 1
    res_matched = 2
    res_continue = 3

    def match(self, form):
        raise RuntimeError('unimplemented')

    def new_copy(self):
        raise RuntimeError('unimplemented')

    def clone(self):
        raise RuntimeError('unimplemented')

    def is_applicable(self, rtme, other_rtme):
        raise RuntimeError('unimplemented')

    def apply_on(self, rtme, other_rtme):
        raise RuntimeError('unimplemented')

    def always_pending(self):
        raise RuntimeError('unimplemented')

    def ignore_pending_state(self):
        raise RuntimeError('unimplemented')

    def get_info(self):
        raise RuntimeError('unimplemented')


class RtDynamicRule(RtRule):
    def match(self, form):
        raise RuntimeError('not applicable')


class RtStaticRule(RtRule):
    def is_applicable(self, rtme, other_rtme):
        raise RuntimeError('not applicable')

    def apply_on(self, rtme, other_rtme):
        raise RuntimeError('not applicable')

    def always_pending(self):
        raise RuntimeError('not applicable')

    def ignore_pending_state(self):
        raise RuntimeError('not applicable')

    def get_info(self):
        raise RuntimeError('unimplemented')


class c__pos_check(RtStaticRule):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def match(self, form):
        return form.get_pos() in self.__pos_names


class c__pos_check_inv(RtStaticRule):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def match(self, form):
        return form.get_pos() not in self.__pos_names


class c__pos_syntax_check(RtStaticRule):
    def __init__(self, syntax_name):
        assert syntax_name in ['comma', 'dot', 'question'], 'Unsupported syntax {0}'.format(syntax_name)
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
        return RtRuleFactory(c__pos_check, ["noun", ])

    def IsAdjective(self):
        return RtRuleFactory(c__pos_check, ["adjective", ])

    def IsAdverb(self):
        return RtRuleFactory(c__pos_check, ["adverb", ])

    def IsVerb(self):
        return RtRuleFactory(c__pos_check, ["verb", ])

    def IsSuject(self):
        return RtRuleFactory(c__pos_check, ["noun", "pronoun"])

    def IsComma(self):
        return RtRuleFactory(c__pos_syntax_check, "comma")

    def IsExcept(self, pos_names):
        return RtRuleFactory(c__pos_check_inv, pos_names)


class c__word_check(RtStaticRule):
    def __init__(self, words):
        self.__words = words

    def match(self, form):
        return form.get_word() in self.__words


class WordSpecs(object):
    def IsWord(self, words):
        return RtRuleFactory(c__word_check, words)


class c__case_check(RtStaticRule):
    def __init__(self, cases):
        self.__cases = cases

    def match(self, form):
        return form.get_case() in self.__cases


class CaseSpecs(object):
    def IsCase(self, cases):
        return RtRuleFactory(c__case_check, cases)


class c__position_spec(RtDynamicRule):
    def __init__(self, anchor=None):
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

    def always_pending(self):
        return False

    def ignore_pending_state(self):
        return False

    def get_info(self):
        return 'id_name: {0}, always_pending: {1}, ignore_pend_state: {2}'.format(self.__anchor, self.always_pending(), self.ignore_pending_state())


class c__position_fini(RtDynamicRule):
    def __init__(self, anchor=None):
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


class PositionSpecs(object):
    def IsBefore(self, anchor):
        return RtRuleFactory(c__position_spec, anchor=anchor)

    def SequenceEnd(self, anchor='fini'):
        return RtRuleFactory(c__position_fini, anchor=anchor)

    def IsBeforeIfExists(self, anchor):
        return RtRuleFactory(c__position_spec, anchor=anchor)


class c__slave_master_spec(RtDynamicRule):
    def __init__(self, anchor=None):
        self.__anchor = RtMatchString(anchor)

    def new_copy(self):
        return c__slave_master_spec(self.__anchor)

    def clone(self):
        return c__slave_master_spec(self.__anchor)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        return RtRule.res_matched if other_rtme.get_form() in rtme.get_form().get_master_forms() else RtRule.res_failed

    def always_pending(self):
        return False

    def ignore_pending_state(self):
        return False

    def get_info(self):
        return 'id_name: {0}, always_pending: {1}, ignore_pend_state: {2}'.format(self.__id_name, self.always_pending(), self.ignore_pending_state())


class c__slave_master_unwanted_spec(RtDynamicRule):
    def __init__(self, anchor):
        self.__anchor = RtMatchString(anchor)

    def new_copy(self):
        return c__slave_master_unwanted_spec(self.__anchor)

    def clone(self):
        return c__slave_master_unwanted_spec(self.__anchor)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def apply_on(self, rtme, other_rtme):
        slave = rtme.get_form()
        master = other_rtme.get_form()
        for m, l in slave.get_masters():
            if m != master:
                rtme.add_unwanted_link(l)

        return RtRule.res_matched

    def always_pending(self):
        return True

    def ignore_pending_state(self):
        return True

    def get_info(self):
        return 'id_name: {0}, always_pending: {1}, ignore_pend_state: {2}'.format(self.__anchor, self.always_pending(), self.ignore_pending_state())


class LinkSpecs(object):
    def IsSlave(self, anchor):
        return RtRuleFactory(c__slave_master_spec, anchor=anchor)

    def MastersExcept(self, anchor):
        return RtRuleFactory(c__slave_master_unwanted_spec, anchor=anchor)

    def AllMasters(self):
        return RtRuleFactory(c__slave_master_unwanted_spec, ("__all_masters", ))


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

    def get_info(self):
        return u'fini'

    def get_pos(self):
        return u'fini'


class RtMatchString(object):
    def __init__(self, string):
        assert isinstance(string, str) or isinstance(string, unicode) or isinstance(string, RtMatchString)

        if isinstance(string, RtMatchString):
            self.__init_from_rtmatchstring(string)
        else:
            self.__init_from_string(string)

    def __init_from_string(self, string):
        self.update(string)

    def __init_from_rtmatchstring(self, rtmstr):
        self.__raw_string = rtmstr.__raw_string
        self.__string = rtmstr.__string
        self.__need_resolve = rtmstr.__need_resolve
        self.__need_reindex = rtmstr.__need_reindex

    def update(self, string):
        self.__raw_string = string
        self.__need_resolve = '$' in self.__raw_string
        self.__need_reindex = '{' in self.__raw_string
        self.__string = self.__raw_string if not self.__need_resolve and not self.__need_reindex else None

    def need_resolve(self):
        return self.__need_resolve

    def need_reindex(self):
        return self.__need_reindex

    def __cmp__(self, other):
        assert not self.__need_resolve and not self.__need_reindex and not other.__need_resolve and not other.__need_reindex
        return cmp(self.__string, other.__string)

    def __eq__(self, other):
        assert isinstance(other, RtMatchString)
        assert not self.__need_resolve and not self.__need_reindex and not other.__need_resolve and not other.__need_reindex, (self.__raw_string, self.__string, other.__raw_string, other.__string)
        return self.__string == other.__string

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__string if not self.__need_resolve and not self.__need_reindex else self.__raw_string

    def __hash__(self):
        return hash(self.__repr__())


class RtRuleFactory(object):
    def __init__(self, classname, *args, **kwargs):
        self.__classname = classname
        self.__args = args
        self.__kwargs = {k: w if '$' not in w else RtMatchString(w) for k, w in kwargs.items()}

    def create(self, compiler, state):
        kwargs = {}
        for k, w in self.__kwargs.items():
            if isinstance(w, RtMatchString) and w.need_resolve():
                w = RtMatchString(w)
                w.update(compiler.resolve_name(state, str(w)))
            kwargs[k] = w
        return self.__classname(*self.__args, **kwargs)
