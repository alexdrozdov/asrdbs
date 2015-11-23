#!/usr/bin/env python
# -*- #coding: utf8 -*-


import re
import matcher
from argparse import Namespace as ns
from matchcmn import MatchBool


class SequenceSpec(object):
    def __init__(self, name):
        self.__name = name

    def get_spec(self):
        return self.spec

    def get_name(self):
        return self.__name

    def get_validate(self):
        return None


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

    def get_info(self, wrap=False):
        raise RuntimeError('unimplemented')

    def has_bindings(self):
        raise RuntimeError('unimplemented')

    def get_bindings(self):
        raise RuntimeError('unimplemented')

    def is_static(self):
        raise RuntimeError('unimplemented')


class RtDynamicRule(RtRule):
    def __init__(self, optional=False, persistent=False):
        assert not persistent or optional, "persistent rule must be optional, either all entries will fail"
        self.__optional = optional
        self.__persistent = persistent

    def match(self, form):
        raise RuntimeError('not applicable')

    def has_bindings(self):
        raise RuntimeError('unimplemented')

    def get_bindings(self):
        raise RuntimeError('unimplemented')

    def is_static(self):
        return False

    def is_optional(self):
        return self.__optional

    def is_persistent(self):
        return self.__persistent


class RtStaticRule(RtRule):
    def is_applicable(self, rtme, other_rtme):
        raise RuntimeError('not applicable')

    def apply_on(self, rtme, other_rtme):
        raise RuntimeError('not applicable')

    def is_optional(self):
        raise RuntimeError('not applicable')

    def is_persistent(self):
        raise RuntimeError('not applicable')

    def has_bindings(self):
        return False

    def get_bindings(self):
        return []

    def is_static(self):
        return True


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
        return form.get_case() in self.__cases

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
        res = matcher.matcher.match(other_form, rtme_form)
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
            'reliability': self.__weight,
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


class SpecStateIniForm(object):
    def __init__(self):
        pass

    def get_word(self):
        return u'ini'

    def get_pos(self):
        return u'ini'

    def get_uniq(self):
        return 0

    def clone_without_links(self):
        return SpecStateIniForm()


class SpecStateFiniForm(object):
    def __init__(self):
        pass

    def get_word(self):
        return u'fini'

    def get_info(self):
        return u'fini'

    def get_pos(self):
        return u'fini'

    def get_uniq(self):
        return 0

    def clone_without_links(self):
        return SpecStateIniForm()


class SentanceFini(object):
    def __init__(self):
        self.__entries = [SpecStateFiniForm()]

    def get_word(self):
        return u'fini'

    def get_uniq(self):
        return 0

    def get_forms(self):
        return self.__entries


class RtMatchString(object):
    def __init__(self, string, max_level=None):
        assert isinstance(string, str) or isinstance(string, unicode) or isinstance(string, RtMatchString)

        if isinstance(string, RtMatchString):
            self.__init_from_rtmatchstring(string, max_level)
        else:
            self.__init_from_string(string, max_level)

    def __init_from_string(self, string, max_level):
        self.__raw_string = string
        self.__need_resolve = '$' in self.__raw_string
        self.__need_reindex = '{' in self.__raw_string
        self.__is_re = '\\d+' in self.__raw_string
        self.__max_level = max_level
        self.__string = self.__raw_string if not self.__need_resolve and not self.__need_reindex and not self.__is_re else None
        self.__re = None if not self.__is_re else re.compile(self.__raw_string)

    def __init_from_rtmatchstring(self, rtmstr, max_level):
        self.__raw_string = rtmstr.__raw_string
        self.__string = rtmstr.__string
        self.__re = rtmstr.__re
        self.__need_resolve = rtmstr.__need_resolve
        self.__need_reindex = rtmstr.__need_reindex
        self.__is_re = rtmstr.__is_re
        self.__max_level = max_level if max_level is not None else rtmstr.__max_level

    def get_max_level(self):
        return self.__max_level

    def update(self, string):
        assert isinstance(string, str) or isinstance(string, unicode) or isinstance(string, RtMatchString)
        if isinstance(string, RtMatchString):
            self.__init_from_rtmatchstring(string, self.__max_level)
        else:
            self.__init_from_string(string, self.__max_level)

    def need_resolve(self):
        return self.__need_resolve

    def need_reindex(self):
        return self.__need_reindex

    def __cmp__(self, other):
        assert not self.__need_resolve and not self.__need_reindex and not other.__need_resolve and not other.__need_reindex and not self.__is_re and not other.__is_re
        return cmp(self.__string, other.__string)

    def __eq__(self, other):
        assert isinstance(other, RtMatchString)
        assert not self.__need_resolve and not self.__need_reindex and not other.__need_resolve and not other.__need_reindex and not (self.__is_re and other.__is_re), (self.__raw_string, self.__string, other.__raw_string, other.__string)
        if not self.__is_re and not other.__is_re:
            return self.__string == other.__string
        if self.__is_re:
            return self.__re.match(other.__string) is not None
        if other.__is_re:
            return other.__re.match(self.__string) is not None

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__string if not self.__need_resolve and not self.__need_reindex and not self.__is_re else self.__raw_string

    def __hash__(self):
        return hash(self.__repr__())


class SameDictList(object):
    def __init__(self):
        self.__dicts = [{}, ]

    def __setitem__(self, key, value):
        assert isinstance(value, list)
        d_len = len(self.__dicts)
        v_len = len(value)
        self.__grow(d_len * v_len)
        if v_len == 1:
            for d in self.__dicts:
                d[key] = value[0]
        else:
            for i in range(d_len):
                for j in range(v_len):
                    self.__dicts[i * v_len + j][key] = value[j]

    def __grow(self, new_size):
        d_len = len(self.__dicts)
        if d_len == new_size:
            return
        grow_factor = new_size / d_len
        for i in range(grow_factor - 1):
            for j in range(d_len):
                d = {k: w if not isinstance(w, str) or '$' not in w else RtMatchString(w) for k, w in self.__dicts[j].items()}
                self.__dicts.append(d)

    def __getitem__(self, key):
        return self.__dicts[0][key]

    def get_dicts(self):
        return self.__dicts


class RtRuleFactory(object):
    def __init__(self, classname, *args, **kwargs):
        if isinstance(classname, RtRuleFactory):
            max_level = None
            if 'max_level' in kwargs:
                max_level = kwargs['max_level']
            self.__init_from_factory(classname, max_level=max_level)
        else:
            self.__init_from_params(classname, args, kwargs)

    def __init_from_factory(self, rrf, max_level):
        assert not rrf.__created
        self.__classname = rrf.__classname
        self.__max_level = max_level if max_level is not None else rrf.__max_level
        self.__args = rrf.__args
        self.__kwargs = {k: RtMatchString(w) if isinstance(w, RtMatchString) else w for k, w in rrf.__kwargs.items()}
        self.__created = False

    def __init_from_params(self, classname, args, kwargs):
        self.__classname = classname
        self.__max_level = None
        self.__args = args  # FIXME Some strange logic in the next line
        self.__kwargs = {k: w if not isinstance(w, str) or '$' not in w else RtMatchString(w) for k, w in kwargs.items()}
        self.__created = False

    def create(self, compiler, state):
        assert not self.__created
        self.__created = True
        max_level = state.get_glevel() if self.__max_level is None else min(self.__max_level, state.get_glevel())
        kwargs = SameDictList()
        for k, w in self.__kwargs.items():
            if isinstance(w, RtMatchString) and w.need_resolve():
                n = compiler.resolve_variant_count(state.get_spec(), str(w))
                if n == 1:
                    w = RtMatchString(w, max_level=max_level)
                    w.update(compiler.resolve_name(state.get_spec(), str(w)))
                    ww = [w, ]
                else:
                    ww = []
                    for i in range(n):
                        w_ = RtMatchString(w, max_level)
                        w_.update(compiler.resolve_name(state.get_spec(), str(w_), i))
                        ww.append(w_)
            else:
                ww = [w, ]
            kwargs[k] = ww
        rules = []
        for kw in kwargs.get_dicts():
            r = self.__classname(*self.__args, **kw)
            if r.has_bindings():
                for b in r.get_bindings():
                    if compiler.binding_needs_resolve(b):
                        b.update(compiler.resolve_binding(b))
            rules.append(r)
        return rules

    def created(self):
        return self.__created


class ValidatePresence(object):
    def __init__(self, spec, required_names):
        self.__spec_name = spec.get_name()
        self.__required_names = [self.__resolve_name(name) for name in required_names]

    def __resolve_name(self, name):
        if '$SPEC' in name:
            return name.replace('$SPEC', '::' + self.__spec_name)
        return name

    def validate(self, sequence):
        for name in self.__required_names:
            if not sequence.has_item(starts_with=name):
                return False
        return True


class ValidateAll(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        for v in self.__validators:
            if not v.validate(sequence):
                return False
        return True


class ValidateAny(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        for v in self.__validators:
            if v.validate(sequence):
                return True
        return False


class ValidateNone(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        for v in self.__validators:
            if v.validate(sequence):
                return False
        return True


class ValidateOne(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        r = False
        for v in self.__validators:
            if v.validate(sequence):
                if r:
                    return False
                r = True
        return r


class LinkWeight(object):
    def __init__(self, ref_name):
        self.__ref_name = ref_name
