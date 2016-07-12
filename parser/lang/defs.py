#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.matcher
import parser.selectors
from parser.lang.common import RtRuleFactory, RtRule
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


class RtAnchorRelated(parser.lang.common.RtDynamicRule):
    def __init__(self, anchor, optional=False, persistent=False):
        super(RtAnchorRelated, self).__init__(
            optional=optional, persistent=persistent
        )
        self.__anchor = parser.lang.common.RtMatchString(anchor)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, parser.lang.common.RtMatchString)
        if other_name == self.__anchor:
            return True
        return False

    def anchor(self):
        return self.__anchor

    def has_bindings(self):
        return True

    def get_bindings(self):
        return [self.__anchor, ]


class BasicDynamicRule(RtAnchorRelated):
    def __init__(self, name, friendly, anchor, optional, persistent, weight):
        super(BasicDynamicRule, self).__init__(
            anchor, optional=optional, persistent=persistent
        )
        self.__name = name
        self.__friendly = friendly
        self.__weight = weight

    def name(self):
        return self.__name

    def friendly(self):
        return self.__friendly

    def weight(self):
        return self.__weight

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        elif fmt == 'dot-html':
            return self.__format_dot()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __format_dot(self):
        wrap = u'<BR ALIGN="LEFT"/>'
        s = u'{0}{1}'.format(self.name(), wrap)
        s += u' anchor: {0}{1}'.format(self.anchor(), wrap)
        s += u' is_persistent: {0}{1}'.format(self.is_persistent(), wrap)
        s += u' is_optional: {0}{1}'.format(self.is_optional(), wrap)
        return s

    def __format_dict(self):
        return {
            'rule': self.name(),
            'friendly': self.friendly(),
            'anchor': self.anchor(),
            'reliability': self.weight(),
            'is_persistent': self.is_persistent(),
            'is_optional': self.is_optional(),
        }

    def __repr__(self):
        return "{0}(objid={1}, anchor='{2}')".format(
            self.friendly(),
            hex(id(self)),
            self.anchor()
        )

    def __str__(self):
        return "{0}(objid={1}, anchor='{2}')".format(
            self.friendly(),
            hex(id(self)),
            self.anchor()
        )


class c__exclusive_with_spec(BasicDynamicRule):
    def __init__(self, anchor):
        super(c__exclusive_with_spec, self).__init__(
            name='exclusive-with',
            friendly='ExclusiveWith',
            anchor=anchor,
            optional=True,
            persistent=False,
            weight=1.0
        )

    def new_copy(self):
        return c__exclusive_with_spec(self.anchor())

    def clone(self):
        return c__exclusive_with_spec(self.anchor())

    def apply_on(self, rtme, other_rtme, link_creators=None):
        other_rtme.close_aggregator()
        return RtRule.res_failed


class AnchorSpecs(object):
    no_anchor = 0
    local_spec_anchor = 1
    local_spec_tag = 2
    global_anchor = 3

    def LocalSpecAnchor(self, name=None):
        return (True, AnchorSpecs.local_spec_anchor, name)

    def Tag(self, name):
        return (True, AnchorSpecs.local_spec_tag, name)

    def ExclusiveWith(self, anchor):
        return RtRuleFactory(c__exclusive_with_spec, anchor=anchor)


class BasicStaticRule(parser.lang.common.RtStaticRule):
    def __init__(self, name, friendly, fmt_info):
        super(BasicStaticRule, self).__init__()
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
        wrap = u'<BR ALIGN="LEFT"/>'
        s = u'{0}{1}'.format(self.name(), wrap)
        s += wrap.join(
            map(
                lambda (k, v): u'{0}: {1}'.format(unicode(k), unicode(v)),
                self.__fmt_info.items()
            )
        )
        return s

    def __format_dict(self):
        return dict(
            [
                ('rule', self.name()),
                ('friendly', self.friendly())
            ] + self.__fmt_info.items()
        )

    def __repr__(self):
        return "{0}(objid={1}, anchor='{2}')".format(
            self.friendly(),
            hex(id(self)),
            self.anchor()
        )

    def __str__(self):
        return "{0}(objid={1}, anchor='{2}')".format(
            self.friendly(),
            hex(id(self)),
            self.anchor()
        )


class c__pos_check(BasicStaticRule):
    def __init__(self, pos_names):
        super(c__pos_check, self).__init__(
            name='pos',
            friendly='IsPos',
            fmt_info={u'pos': pos_names}
        )
        self.__pos_names = pos_names

    def new_copy(self):
        return c__pos_check(self.__pos_names)

    def match(self, form):
        return form.get_pos() in self.__pos_names

    def get_info(self, wrap=False):
        return u'pos: {0}'.format(self.__pos_names[0])


class c__pos_check_inv(BasicStaticRule):
    def __init__(self, pos_names):
        super(c__pos_check_inv, self).__init__(
            name='pos-inv',
            friendly='IsNotPos',
            fmt_info={u'pos': pos_names}
        )
        self.__pos_names = pos_names

    def new_copy(self):
        return c__pos_check_inv(self.__pos_names)

    def match(self, form):
        return form.get_pos() not in self.__pos_names

    def get_info(self, wrap=False):
        return u'not pos: {0}'.format(self.__pos_names[0])


class c__placeholder(BasicStaticRule):
    def __init__(self, def_value):
        super(c__placeholder, self).__init__(
            name='placeholder',
            friendly='Placeholder',
            fmt_info={u'value': def_value}
        )
        self.__def_value = def_value

    def new_copy(self):
        return c__placeholder(self.__def_value)

    def match(self, form):
        return self.__def_value

    def get_info(self, wrap=False):
        return u'placeholder: {0}'.format(self.__def_value)


class c__pos_syntax_check(BasicStaticRule):
    def __init__(self, syntax_name):
        super(c__pos_syntax_check, self).__init__(
            name='syntax',
            friendly='IsSyntax',
            fmt_info={u'syntax': syntax_name}
        )
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
    def IsPos(self, pos):
        if not isinstance(pos, (list, tuple)):
            pos = [pos, ]
        return RtRuleFactory(c__pos_check, pos)

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

    def IsAnimated(self):
        return RtRuleFactory(c__placeholder, False)

    def IsInanimated(self):
        return RtRuleFactory(c__placeholder, False)


class c__word_check(BasicStaticRule):
    def __init__(self, words):
        super(c__word_check, self).__init__(
            name='word',
            friendly='IsWord',
            fmt_info={u'word': words}
        )
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


class c__case_check(BasicStaticRule):
    def __init__(self, cases):
        super(c__case_check, self).__init__(
            name='case',
            friendly='IsCase',
            fmt_info={u'pos': cases}
        )
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


class c__position_spec(BasicDynamicRule):
    def __init__(self, anchor):
        super(c__position_spec, self).__init__(
            name='position',
            friendly='Position',
            anchor=anchor,
            optional=False,
            persistent=False,
            weight=1.0
        )

    def new_copy(self):
        return c__position_spec(self.anchor())

    def clone(self):
        return c__position_spec(self.anchor())

    def apply_on(self, rtme, other_rtme, link_creators=None):
        return RtRule.res_matched if rtme.get_form().get_position() < other_rtme.get_form().get_position() else RtRule.res_failed


class c__position_fini_spec(BasicDynamicRule):
    def __init__(self, anchor=None):
        super(c__position_fini_spec, self).__init__(
            name='position-fini',
            friendly='PositionFini',
            anchor=anchor,
            optional=False,
            persistent=False,
            weight=1.0
        )

    def new_copy(self):
        return c__position_fini_spec(self.anchor())

    def clone(self):
        return c__position_fini_spec(self.anchor())

    def apply_on(self, rtme, other_rtme, link_creators=None):
        return RtRule.res_matched if rtme.get_form().get_position() == other_rtme.get_form().get_position() else RtRule.res_failed


class PositionSpecs(object):
    def IsBefore(self, anchor):
        return RtRuleFactory(c__position_spec, anchor=anchor)

    def SequenceEnd(self, anchor='fini'):
        return RtRuleFactory(c__position_fini_spec, anchor=anchor)

    def IsBeforeIfExists(self, anchor):
        return RtRuleFactory(c__position_spec, anchor=anchor)


class c__sameas_spec(BasicDynamicRule):
    def __init__(self, anchor=None, get_param_fcn=None, param_name=None):
        super(c__sameas_spec, self).__init__(
            name='same-as',
            friendly='SameAs',
            anchor=anchor,
            optional=False,
            persistent=False,
            weight=1.0
        )

        assert get_param_fcn is not None
        self.__get_param_fcn = get_param_fcn
        self.__param_name = param_name

    def new_copy(self):
        return c__sameas_spec(self.anchor(), self.__get_param_fcn, self.__param_name)

    def clone(self):
        return c__sameas_spec(self.anchor(), self.__get_param_fcn, self.__param_name)

    def apply_on(self, rtme, other_rtme, link_creators=None):
        return RtRule.res_matched if self.__get_param_fcn(rtme) == self.__get_param_fcn(other_rtme) else RtRule.res_failed


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


class c__slave_master_spec(BasicDynamicRule):
    def __init__(self, anchor=None, weight=None):
        super(c__slave_master_spec, self).__init__(
            name='master-slave',
            friendly='MasterSlave',
            anchor=anchor,
            optional=True,
            persistent=False,
            weight=weight
        )

    def new_copy(self):
        return c__slave_master_spec(self.anchor(), self.weight())

    def clone(self):
        return c__slave_master_spec(self.anchor(), self.weight())

    def apply_on(self, rtme, other_rtme, link_creators=None):
        rtme_form = rtme.get_form()
        other_form = other_rtme.get_form()
        res = parser.matcher.match(other_form, rtme_form)
        if res:
            rtme.add_link(
                [
                    ns(master=other_rtme, slave=rtme, details=res.to_dict(), track_revisions=False),
                    ns(master=other_rtme, slave=rtme, details=self.foramt('dict'), track_revisions=False),
                ]
            )
        return RtRule.res_matched if res else RtRule.res_failed


class c__slave_master_unwanted_spec(BasicDynamicRule):
    def __init__(self, anchor, weight=None):
        super(c__slave_master_unwanted_spec, self).__init__(
            name='unwanted-links',
            friendly='UnwantedExcept',
            anchor=anchor,
            optional=True,
            persistent=True,
            weight=weight
        )

    def new_copy(self):
        return c__slave_master_unwanted_spec(self.anchor(), self.weight())

    def clone(self):
        return c__slave_master_unwanted_spec(self.anchor(), self.weight())

    def apply_on(self, rtme, other_rtme, link_creators=None):
        return RtRule.res_matched

        slave = rtme.get_form()
        master = other_rtme.get_form()
        for m, l in slave.get_masters():
            if m != master:
                rtme.add_unwanted_link(l, weight=self.__weight, rule=self)


class LinkSpecs(object):
    def IsSlave(self, anchor, weight=None):
        return RtRuleFactory(c__slave_master_spec, anchor=anchor, weight=weight)

    def MastersExcept(self, anchor, weight=None):
        return RtRuleFactory(c__slave_master_unwanted_spec, anchor=anchor, weight=weight)

    def AllMasters(self, weight=None):
        return RtRuleFactory(c__slave_master_unwanted_spec, ("__all_masters", ))


class c__refersto_spec(BasicDynamicRule):
    def __init__(self, anchor):
        super(c__refersto_spec, self).__init__(
            name='refers-to',
            friendly='RefersTo',
            anchor=anchor,
            optional=False,
            persistent=False,
            weight=1.0
        )

    def new_copy(self):
        return c__refersto_spec(self.anchor())

    def clone(self):
        return c__refersto_spec(self.anchor())

    def apply_on(self, rtme, aggregator_rtme, link_creators=None):
        aggregator_rtme.attach_referer(rtme)
        rtme.add_link(
            [
                ns(master=aggregator_rtme, slave=rtme, qualifiers={},
                   debug=self.format('dict'), track_revisions=False),
            ]
        )
        return RtRule.res_matched


class RefersToSpecs(object):
    def AttachTo(self, anchor):
        return RtRuleFactory(
            c__refersto_spec,
            anchor=anchor
        )


class c__dependencyof_spec(BasicDynamicRule):
    def __init__(self, anchor=None, dependency_class=None, weight=1.0):
        super(c__dependencyof_spec, self).__init__(
            name='dependency-of',
            friendly='DependencyOf',
            anchor=anchor,
            optional=True,
            persistent=False,
            weight=weight
        )

        self.__dep_class = dependency_class
        if dependency_class is not None:
            self.__dep_selector = parser.selectors.selector(dependency_class)
        else:
            self.__dep_selector = None

    def new_copy(self):
        return c__dependencyof_spec(
            self.anchor(),
            self.__dep_class,
            self.weight()
        )

    def clone(self):
        return c__dependencyof_spec(
            self.anchor(),
            self.__dep_class,
            self.weight()
        )

    def apply_on(self, rtme, other_rtme, link_creators=None):
        rtme_form = rtme.get_form()
        other_form = other_rtme.get_form()
        res = parser.matcher.match(other_form, rtme_form)
        if not res:
            return RtRule.res_failed
        if res:
            if self.__dep_selector is None:
                self.__mk_unqualified_link(rtme, other_rtme, res)
                return RtRule.res_matched
            sres = self.__dep_selector(
                rtme_form,
                other_form
            )
            if not sres:
                return RtRule.res_failed
            self.__mk_qualified_link(rtme, other_rtme, res, sres)
            return RtRule.res_matched

    def __mk_qualified_link(self, rtme, other_rtme, res, sres):
        rtme.add_link(
            [
                self.__mk_link(other_rtme, rtme, info=self.format('dict')),
                self.__mk_link(other_rtme, rtme, created_by='grammatics',
                               info=res.to_dict()
                               ),
                self.__mk_link(
                    other_rtme,
                    rtme,
                    created_by=self.__dep_class,
                    qualifiers=sres.link_attrs,
                    info=sres.info,
                    track_revisions=True
                ),
            ]
        )

    def __mk_unqualified_link(self, rtme, other_rtme, res):
        rtme.add_link(
            [
                self.__mk_link(other_rtme, rtme, created_by='grammatics',
                               info=self.format('dict')
                               ),
                self.__mk_link(other_rtme, rtme, info=res.to_dict()),
            ]
        )

    def __mk_link(self, master, slave, created_by=None, qualifiers=None,
                  info=None, track_revisions=False, rewrite_existing=True):
        if created_by is not None:
            created_by = self.__class__.__name__ + '/' + created_by
        else:
            created_by = self.__class__.__name__
        if qualifiers is None:
            qualifiers = {}
        if info is None:
            info = {}
        return ns(
            master=master,
            slave=slave,
            created_by=self.__class__.__name__,
            qualifiers=qualifiers,
            debug=info,
            track_revisions=track_revisions,
            rewrite_existing=rewrite_existing
        )


class DependencySpecs(object):
    def DependencyOf(self, anchor, dependency_class=None, weight=None):
        if not dependency_class.startswith('#'):
            dependency_class = None

        return RtRuleFactory(
            c__dependencyof_spec,
            anchor=anchor,
            dependency_class=dependency_class,
            weight=weight
        )


class c__aggregate_close_spec(BasicDynamicRule):
    def __init__(self, anchor=None):
        super(c__aggregate_close_spec, self).__init__(
            name='aggregate-close',
            friendly='CloseWith',
            anchor=anchor,
            optional=False,
            persistent=False,
            weight=1.0
        )

    def new_copy(self):
        return c__aggregate_close_spec(self.anchor())

    def clone(self):
        return c__aggregate_close_spec(self.anchor())

    def apply_on(self, rtme, other_rtme, link_creators=None):
        rtme.close_aggregator()
        return RtRule.res_matched


class c__aggregate_close_other_spec(BasicDynamicRule):
    def __init__(self, anchor=None):
        super(c__aggregate_close_other_spec, self).__init__(
            name='aggregate-close-other',
            friendly='CloseOther',
            anchor=anchor,
            optional=False,
            persistent=False,
            weight=1.0
        )

    def new_copy(self):
        return c__aggregate_close_other_spec(self.anchor())

    def clone(self):
        return c__aggregate_close_other_spec(self.anchor())

    def apply_on(self, rtme, other_rtme, link_creators=None):
        other_rtme.close_aggregator()
        return RtRule.res_matched


class AggregateSpecs(object):
    def Close(self, anchor):
        return RtRuleFactory(c__aggregate_close_other_spec, anchor=anchor)

    def CloseWith(self, anchor):
        return RtRuleFactory(c__aggregate_close_spec, anchor=anchor)


class c__selector(BasicStaticRule):
    def __init__(self, selector):
        super(c__selector, self).__init__(
            name='selector',
            friendly='Selector',
            fmt_info={u'selector': selector}
        )
        self.__selector = selector

    def new_copy(self):
        return c__selector(self.__selector)

    def match(self, form):
        return self.__selector(form, can_modify=True)

    def get_info(self, wrap=False):
        return u'selector: {0}'.format(str(self.__selector))


class SelectorSpecs(object):
    def Selector(self, name):
        return RtRuleFactory(c__selector, parser.selectors.selector(name))
