#!/usr/bin/env python
# -*- #coding: utf8 -*-


import re


class SequenceSpec(object):
    def __init__(self, name, spec=None):
        self.__name = name
        self.__compared_with = {}
        self.spec = spec

    def get_spec(self):
        return self.spec

    def get_name(self):
        return self.__name

    def get_validate(self):
        return None

    def format(self, fmt):
        if fmt == 'dict':
            return self.__fmt_dict()
        raise Exception('Not implemented')

    def __fmt_dict(self):
        return {
            'name': self.get_name(),
            'entries': self.__plain(self.spec)
        }

    def __plain(self, obj):
        if isinstance(obj, dict):
            return self.__plain_dict(obj)
        if isinstance(obj, (list, tuple)):
            return self.__plain_list(obj)
        if isinstance(obj, (int, bool)):
            return obj
        if hasattr(obj, 'format'):
            return obj.format('dict')
        return str(obj)

    def __plain_dict(self, obj):
        return {k: self.__plain(v) for k, v in obj.items()}

    def __plain_list(self, obj):
        return [self.__plain(i) for i in obj]


class RtRule(object):
    res_none = 0
    res_failed = 1
    res_matched = 2
    res_continue = 3

    def __init__(self):
        super(RtRule, self).__init__()

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

    def format(self, fmt):
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
    def __init__(self):
        super(RtStaticRule, self).__init__()

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


class RtAnchorRelated(RtDynamicRule):
    def __init__(self, anchor, optional=False, persistent=False):
        super(RtAnchorRelated, self).__init__(
            optional=optional, persistent=persistent
        )
        self.__anchor = RtMatchString(anchor)

    def is_applicable(self, rtme, other_rtme):
        other_name = other_rtme.get_name()
        assert isinstance(other_name, RtMatchString)
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
        wrap = '<BR ALIGN="LEFT"/>'
        s = '{0}{1}'.format(self.name(), wrap)
        s += ' anchor: {0}{1}'.format(self.anchor(), wrap)
        s += ' is_persistent: {0}{1}'.format(self.is_persistent(), wrap)
        s += ' is_optional: {0}{1}'.format(self.is_optional(), wrap)
        return s

    def __format_dict(self):
        return {
            'rule': self.name(),
            'friendly': self.friendly(),
            'anchor': str(self.anchor()),
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


class BasicStaticRule(RtStaticRule):
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
        wrap = '<BR ALIGN="LEFT"/>'
        s = '{0}{1}'.format(self.name(), wrap)
        s += wrap.join(
            ['{0}: {1}'.format(str(k_v[0]), str(k_v[1]))
             for k_v in list(self.__fmt_info.items())
             ]
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
            ['{0}: {1}'.format(str(k_v[0]), str(k_v[1]))
             for k_v in list(self.__fmt_info.items())
             ]
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


class UnresolvedDynamicInclude(object):
    def __init__(self, name):
        self.__name = name

    def get_name(self):
        return self.__name


class CombinatorialSelectorRule(SelectorStaticRule):
    def __init__(self, name, rules):
        super().__init__(name=name, friendly=name, fmt_info={})
        if rules is None:
            rules = []
        self.__rules = rules

    def subrules(self):
        return self.__rules

    def replace(self, rule, new_rule):
        self.__rules[self.__rules.index(rule)] = new_rule

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        elif fmt == 'dot-html':
            return self.__format_dot()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __format_dict(self):
        return {
            'rule': self.name(),
            'friendly': self.friendly(),
            'sub': [subrule.format('dict') for subrule in self.subrules()]
        }

    def __format_dot(self):
        wrap = '<BR ALIGN="LEFT"/>'
        s = '{0}{1}'.format(self.name(), wrap)
        s += wrap.join(
            ['{0}: {1}'.format(str(k_v[0]), str(k_v[1]))
             for k_v in list(self.__format_dict().items())
             ]
        )
        return s

    def __iadd__(self, other):
        self.__rules.append(other)
        return self

    def __iter__(self):
        return iter(self.subrules())


class RuleNot(CombinatorialSelectorRule):
    def __init__(self, rules):
        super().__init__('not', rules)

    def match(self, *args, **kwargs):
        for r in self.subrules():
            if not r.match(*args, **kwargs):
                return True

        return False


class RuleOr(CombinatorialSelectorRule):
    def __init__(self, rules=None):
        super().__init__('or', rules)

    def match(self, *args, **kwargs):
        for r in self.subrules():
            if r.match(*args, **kwargs):
                return True

        return False

    def new_copy(self):
        return RuleOr(rules=self.subrules())

    def clone(self):
        return RuleOr(rules=self.subrules())


class RuleAnd(CombinatorialSelectorRule):
    def __init__(self, rules=None):
        super().__init__('and', rules)

    def match(self, *args, **kwargs):
        for r in self.subrules():
            if not r.match(*args, **kwargs):
                return False

        return True

    def new_copy(self):
        return RuleAnd(rules=self.subrules())

    def clone(self):
        return RuleAnd(rules=self.subrules())


class RuleXor(CombinatorialSelectorRule):
    def __init__(self, rules=None):
        assert len(rules) == 2
        super().__init__('xor', rules)

    def match(self, *args, **kwargs):
        r1 = self.subrules()[0].match(*args, **kwargs)
        r2 = self.subrules()[1].match(*args, **kwargs)
        return r1 != r2

    def new_copy(self):
        return RuleXor(rules=self.subrules())

    def clone(self):
        return RuleXor(rules=self.subrules())


class RtMatchString(object):
    def __init__(self, string, max_level=None):
        assert isinstance(string, str) or \
            isinstance(string, str) or \
            isinstance(string, RtMatchString), \
            'Unsupported RtMatchstring type {0} ({1})'.format(
                type(string), string)

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
        assert isinstance(string, str) or isinstance(string, str) or isinstance(string, RtMatchString)
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
        grow_factor = int(new_size / d_len)
        for i in range(grow_factor - 1):
            for j in range(d_len):
                d = {k: w if not isinstance(w, str) or '$' not in w else RtMatchString(w) for k, w in list(self.__dicts[j].items())}
                self.__dicts.append(d)

    def __getitem__(self, key):
        return self.__dicts[0][key]

    def get_dicts(self):
        return self.__dicts


class RtRuleFactory(object):
    def __init__(self, classname, *args, **kwargs):
        if isinstance(classname, RtRuleFactory):
            max_level = kwargs.get('max_level', None)
            original_state = kwargs.get('original_state', None)
            self.__init_from_factory(
                classname,
                max_level=max_level,
                original_state=original_state
            )
        else:
            self.__init_from_params(classname, args, kwargs)

    def __init_from_factory(self, rrf, max_level, original_state=None):
        assert not rrf.__created
        self.__classname = rrf.__classname
        self.__max_level = max_level if max_level is not None else rrf.__max_level
        self.__original_state = original_state if rrf.__original_state is None else rrf.__original_state
        self.__args = rrf.__args
        self.__kwargs = {
            k: RtMatchString(w) if isinstance(w, RtMatchString) else w
            for k, w in list(rrf.__kwargs.items())}
        self.__created = False

    def __init_from_params(self, classname, args, kwargs):
        self.__classname = classname
        self.__max_level = None
        self.__original_state = None
        self.__args = args  # FIXME Some strange logic in the next line
        self.__kwargs = {
            k: w if not isinstance(w, str) or '$' not in w else RtMatchString(w)
            for k, w in list(kwargs.items())}
        self.__created = False

    def create(self, compiler, state):
        assert not self.__created
        self.__created = True
        if self.__original_state is not None:
            state = self.__original_state
        max_level = state.get_glevel() if self.__max_level is None else min(
            self.__max_level, state.get_glevel())
        kwargs = SameDictList()
        for k, w in list(self.__kwargs.items()):
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

    def format(self, fmt):
        if fmt == 'dict':
            return self.__fmt_dict()
        raise Exception('Not implemented')

    def __fmt_dict(self):
        return {
            'classname': str(self.__classname),
            'max_level': self.__max_level,
            'original_state': self.__original_state,
            'args': str(self.__args),
            'kwargs': str(self.__kwargs)
        }


class SingleToMultiRuleAdapter(object):
    def __init__(self, rule_cls, indx):
        self.__rule_cls = rule_cls
        self.__indx = indx

    def match(self, *args, **kwargs):
        return self.__rule_cls.match(args[self.__indx])

    def get_info(self, *args, **kwargs):
        return self.__rule_cls.get_info(*args, **kwargs)

    def format(self, *args, **kwargs):
        return self.__rule_cls.format(*args, **kwargs)


class SelectorRuleFactory(object):
    def __init__(self, classname, *args, **kwargs):
        self.__classname = classname
        self.__args = args
        self.__kwargs = kwargs

    def create_single(self):
        return self.__classname(*self.__args, **self.__kwargs)

    def create_multi(self, ref_index):
        return SingleToMultiRuleAdapter(
            self.__classname(*self.__args, **self.__kwargs),
            ref_index
        )


class MultiSelectorRuleFactory(object):
    def __init__(self, classname, *args, **kwargs):
        self.__classname = classname
        self.__args = args
        self.__kwargs = kwargs

    def create_single(self):
        raise RuntimeError(
            'Tried to construct multi selector rule for single-value selector'
        )

    def create_multi(self, ref_index):
        return self.__classname(ref_index, *self.__args, **self.__kwargs)


class LinkWeight(object):
    def __init__(self, ref_name):
        self.__ref_name = ref_name
