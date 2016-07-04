#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import copy
import json
import uuid
import parser.named
import common.config
from common.singleton import singleton
from argparse import Namespace as ns


class SelectorRes(object):
    def __init__(self, res, link_attrs=None, info=None):
        self.res = res
        self.link_attrs = {} if link_attrs is None else link_attrs
        self.info = {} if info is None else info

    def __bool__(self):
        return self.res

    def __nonzero__(self):
        return self.res

    def __and__(self, other):
        if self.res and other.res:
            return SelectorRes(
                True,
                dict(self.link_attrs.items() + other.link_attrs.items()),
                dict(self.info.items() + other.info.items()),
            )
        return SelectorRes(False)

    def __or__(self, other):
        if self.res or other.res:
            return SelectorRes(
                True,
                dict(self.link_attrs.items() + other.link_attrs.items()),
                dict(self.info.items() + other.info.items()),
            )
        return SelectorRes(False)

    def __add__(self, other):
        r = SelectorRes(
            self.res,
            dict(self.link_attrs.items() + other.link_attrs.items()),
            dict(self.info.items() + other.info.items()),
        )
        return r

    def __str__(self):
        return 'SelectorRes({0}, link_attrs={1}, info={2})'.format(
            self.res,
            self.link_attrs,
            self.info
        )

    def __repr__(self):
        return 'SelectorRes({0}, link_attrs={1}, info={2})'.format(
            self.res,
            self.link_attrs,
            self.info
        )


class Selector(object):
    def __init__(self, tags, clarifies, rules):
        assert None not in tags
        assert None not in clarifies
        self.__uniq = uuid.uuid1()
        self.__tags = tags
        self.__clarifies = clarifies
        self.__rules = rules

    def get_tags(self):
        return self.__tags

    def get_uniq(self):
        return self.__uniq

    def apply(self, form):
        return self.__apply(form, test_only=False)

    def test(self, form):
        return self.__apply(form, test_only=True)

    def __apply(self, form, test_only=False):
        for c in self.__clarifies:
            assert c is not None
            if not self.__check_clarify(form, c):
                return self.__failure()
        for r in self.__rules:
            if not r.match(form):
                return self.__failure()
        self.__set_tags(form)
        return SelectorRes(
            True,
            link_attrs={},
            info=self.__list_rules()
        )

    def __list_rules(self):
        return dict(
            reduce(
                lambda x, y: x + y,
                map(
                    lambda r: r.format('dict').items(),
                    self.__rules
                ),
                []
            )
        )

    def __failure(self):
        return SelectorRes(False)

    def __check_clarify(self, form, tag):
        if form.has_tag(tag):
            return True
        selector = Selectors()[tag]
        return selector(form)

    def __set_tags(self, form):
        for t in self.__tags:
            form.add_tag(t, 'morf')

    def __call__(self, *argc, **argv):
        test_only = argv['test_only'] if argv.has_key('test_only') else False
        return self.__apply(argc[0], test_only=test_only)

    def format(self, fmt):
        s = u'<TR><TD BGCOLOR="darkseagreen1">type:selector</TD></TR>'
        s += u'<TR><TD BGCOLOR="darkseagreen1">clarifies: {0}</TD></TR>'.format(
            u' '.join(self.__clarifies)
        )
        s += reduce(
            lambda x, y: x + y,
            map(
                lambda r: u'<TR><TD BGCOLOR="darkseagreen1">{0}</TD></TR>'.format(
                    unicode(r.format('dict'))
                ),
                self.__rules
            ),
            u''
        )
        return s

    def __repr__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )

    def __str__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )


class MultiSelector(object):
    def __init__(self, tags, clarifies, rules, link_attrs, index):
        self.__uniq = uuid.uuid1()
        self.__tags = tags
        self.__clarifies = clarifies
        self.__rules = rules
        self.__link_attrs = link_attrs
        self.__index = index

    def get_tags(self):
        return [t.name for t in self.__tags]

    def get_uniq(self):
        return self.__uniq

    def apply(self, *forms):
        return self.__apply(forms, test_only=False)

    def test(self, *form):
        return self.__apply(form, test_only=True)

    def __failure(self):
        return SelectorRes(False)

    def __apply(self, forms, test_only=False):
        tag_suffix = u'/' + '+'.join(sorted([f.get_uniq() for f in forms]))
        res = SelectorRes(True)
        for c in self.__clarifies:
            res = res and self.__check_clarify(forms, c, tag_suffix)
            if not res:
                return self.__failure()

        for r in self.__rules:
            if not r.match(*forms):
                return self.__failure()

        form = forms[self.__index]
        self.__set_tags(form, tag_suffix)

        return res + SelectorRes(
            False,
            link_attrs=self.__link_attrs,
            info=self.__list_rules()
        )

    def __list_rules(self):
        return dict(
            reduce(
                lambda x, y: x + y,
                map(
                    lambda r: r.format('dict').items(),
                    self.__rules
                ),
                []
            )
        )

    def __check_clarify(self, forms, tag, tag_suffix):
        form = forms[self.__index]
        if form.has_tag(tag) or form.has_tag(tag + tag_suffix):
            return SelectorRes(True)
        selector = Selectors()[tag]
        # fixed_index is required by SelectorHub with single form Selector
        return selector.invoke(*forms, fixed_index=self.__index)

    def __set_tags(self, form, tag_suffix):
        for t in self.__tags:
            tag_name = t.name + tag_suffix if t.auto or t.base else t.name
            form.add_tag(tag_name, 'ctx')

    def __call__(self, *argc, **argv):
        test_only = argv['test_only'] if argv.has_key('test_only') else False
        return self.__apply(argc, test_only=test_only)

    def format(self, fmt):
        s = u'<TR><TD BGCOLOR="darkseagreen1">type: multiselector</TD></TR>'
        s += u'<TR><TD BGCOLOR="darkseagreen1">clarifies: {0}</TD></TR>'.format(
            u' '.join(self.__clarifies)
        )
        s += reduce(
            lambda x, y: x + y,
            map(
                lambda r: u'<TR><TD BGCOLOR="darkseagreen1">{0}</TD></TR>'.format(
                    unicode(r.format('dict'))
                ),
                self.__rules
            ),
            u''
        )
        return s

    def __repr__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )

    def __str__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )


class SelectorHub(object):
    def __init__(self, tag):
        self.__tag = tag
        self.__selectors = []
        self.__is_single = None

    def get_tag(self):
        return self.__tag

    def add_selector(self, selector):
        is_single = isinstance(selector, Selector)
        assert self.__is_single is None or self.__is_single == is_single
        self.__is_single = is_single
        self.__selectors.append(selector)

    def __apply(self, *argc, **argv):
        return reduce(
            lambda x, y: x or y,
            map(
                lambda s: s(*argc, **argv),
                self.__selectors
            ),
            SelectorRes(False)
        )

    def __is_single_selector(self):
        return self.__is_single

    def apply(self, *argc, **argv):
        return self.__apply(*argc, test_only=False)

    def test(self, *argc, **argv):
        return self.__apply(*argc, test_only=True)

    def invoke(self, *args, **argv):
        test_only = argv['test_only'] if 'test_only' in argv else False
        fixed_index = argv['fixed_index'] if 'fixed_index' in argv else None
        if self.__is_single_selector():
            return self.__apply(args[fixed_index], test_only=test_only)
        return self.__apply(*args, test_only=test_only)

    def __call__(self, *argc, **argv):
        return self.__apply(*argc, **argv)

    def __repr__(self):
        return "SelectorHub({0})".format(self.get_tag())

    def __str__(self):
        return "SelectorHub({0})".format(self.get_tag())

    def __iter__(self):
        for s in self.__selectors:
            yield s


class _Preprocessor(object):
    def __init__(self):
        pass

    def preprocess(self, rule):
        rule = copy.deepcopy(rule)

        for d, k, v in self.__iterspec(rule, exclude='clarify'):
            if k[0] == '@':
                self.__handle_tmpl(d, k, v)

        return rule

    def __handle_tmpl(self, d, k, v):
        k = k.replace('@', '')
        tmpl = parser.named.template(k, namespace='selectors')
        tmpl(d)

    def __handle_val_tmpl(self, v):
        return v

    def __iterspec(self, rule, exclude=None):
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude, ]
        keys = filter(
            lambda k: k not in exclude,
            rule.keys(),
        )

        for k in keys:
            v = rule[k]
            if isinstance(v, dict):
                for dd, kk, vv in self.__iterspec(v):
                    yield dd, kk, vv
            elif isinstance(v, list):
                for dd, kk, vv in self.__iterlist(v):
                    yield dd, kk, vv

            yield rule, k, v

    def __iterlist(self, l):
        for i in range(len(l)):
            v = l[i]
            if isinstance(v, str):
                if v[0] == '@':
                    l[i] = self.__handle_val_tmpl(v)
            elif isinstance(v, dict):
                for dd, kk, vv in self.__iterspec(v):
                    yield dd, kk, vv
            elif isinstance(v, list):
                for dd, kk, vv in self.__iterspec(v):
                    yield dd, kk, vv


class _Compiler(object):
    def __init__(self):
        pass

    def compile(self, js, clarifies=None, base_tags=None):
        js = Preprocessor().preprocess(js)
        if clarifies is None:
            clarifies = []
        if u'selector' in js:
            return self.__compile(js[u'selector'], clarifies, base_tags)
        if u'multi' in js:
            return self.__multi(js[u'multi'])
        raise KeyError('neither selector nor multi key found in selector spec')

    def __multi(self, js):
        terms_count = self.__eval_terms_count(js)
        tag_base = map(
            lambda t: ns(
                name=t,
                auto=False,
                base=True
            ),
            self.__get_property_list(js, 'tag-base')
        )
        js = self.__reshape_js_base(js, terms_count)
        index = self.__find_internal_layer(js, terms_count)
        if index is not None:
            index = js.keys()[0]
            js = js[index]
            index = int(index)
            return self.__compile_layer(terms_count, index, js, base_tags=tag_base)
        return []

    def __compile_layer(self, terms_count, index, js, parent_tag=None, base_tags=None):
        base_tags = map(
            lambda t: ns(
                name=t,
                auto=False,
                base=True
            ),
            self.__get_property_list(js, 'tag-base')
        ) + self.__as_list(base_tags, none_is_empty=True)

        tags = map(
            lambda t: ns(
                name=t,
                auto=False,
                base=False
            ),
            self.__get_property_list(js, 'tag')
        )

        clarifies = self.__get_property_list(js, 'clarifies') + \
            self.__as_list(parent_tag, none_is_empty=True)

        if 'link' in js:
            link_attrs = js['link']
        else:
            link_attrs = {}

        rules = reduce(
            lambda x, y: x + y,
            map(
                lambda (r, v): self.__mk_multi_rule(index, r, v),
                self.__rules(js)
            ),
            []
        )

        auto_tag = ns(
            name=u'#' + unicode(uuid.uuid1()),
            auto=True,
            base=False
        )

        selector_tags = tags + [auto_tag, ]
        if link_attrs or tags:
            selector_tags += base_tags

        s = [MultiSelector(
            selector_tags,
            clarifies,
            rules,
            link_attrs,
            index=index
        ), ]

        i_index = self.__find_internal_layer(js, terms_count)
        if i_index is not None:
            i_js = js[unicode(i_index)]
            s.extend(
                self.__compile_layer(
                    terms_count,
                    i_index,
                    i_js,
                    auto_tag.name,
                    base_tags
                )
            )

        clarify = self.__get_property_list(js, 'clarify')
        for c_js in clarify:
            s.extend(
                self.__compile_layer(
                    terms_count,
                    index,
                    c_js,
                    auto_tag.name,
                    base_tags
                )
            )

        return s

    def __find_internal_layer(self, js, terms_count):
        for i in range(terms_count):
            if unicode(i) in js:
                return i
        return None

    def __eval_terms_count(self, js):
        n = 0
        while unicode(n) in js:
            n += 1
        return n

    def __find_deepest_term(self, js, max_count):
        test_set = set(['clarify', ] + [unicode(x) for x in range(max_count)])
        for i in range(max_count):
            t = js[unicode(i)]
            if test_set.intersection(t):
                return i
        raise ValueError('no one item with clarifies found')

    def __reshape_js_base(self, js, terms_count):
        if terms_count is None:
            terms_count = self.__eval_terms_count(js)
        deepest = self.__find_deepest_term(js, terms_count)
        res = {
            unicode(deepest): js[unicode(deepest)]
        }
        for i in range(terms_count):
            if i == deepest:
                continue
            res = {
                unicode(i): dict(js[unicode(i)].items() + res.items())
            }
        return res

    def __compile(self, js, clarifies, base_tags):
        assert base_tags is None or None not in base_tags
        selectors = []

        tags = self.__get_property_list(js, u'tag')
        assert None not in tags
        base_tags = self.__as_list(base_tags, none_is_empty=True) +\
            self.__get_property_list(js, u'tag-base')
        assert None not in base_tags
        clarifies = self.__as_list(clarifies)

        clarifies.extend(self.__get_property_list(js, u'clarifies'))
        rules = reduce(
            lambda x, y: x + y,
            map(
                lambda (r, v): self.__mk_single_rule(r, v),
                self.__rules(js)
            ),
            []
        )

        if tags:
            selectors.append(Selector(tags + base_tags, clarifies, rules))

        for c in self.__get_property_list(js, u'clarify'):
            selectors.extend(self.__compile(c, tags, base_tags))

        return selectors

    def __tags(self, selectors):
        return sorted(list(set(
            reduce(
                lambda x, y: x + y,
                map(
                    lambda s: s.get_tags(),
                    selectors
                ),
                []
            )
        )))

    def __get_property_list(self, js, name, default=None):
        v = [] if default is None else self.__as_list(default)
        if js.has_key(name):
            v = self.__as_list(js[name])
        return v

    def __as_list(self, v, none_is_empty=False):
        if none_is_empty and v is None:
            return []
        if not isinstance(v, list):
            v = [v, ]
        return list(v)

    def __rules(self, js):
        known_rules = [
            'pos', 'case', 'animation',
            'position', 'equal-properties'
        ]
        return map(
            lambda k: (k, js[k]),
            filter(
                lambda k: k in known_rules,
                js.keys()
            )
        )

    def __mk_single_rule(self, k, v):
        if not isinstance(v, list):
            return [v.create_single(), ]
        return map(
            lambda vv: vv.create_single(),
            v
        )

    def __mk_multi_rule(self, index, k, v):
        if not isinstance(v, list):
            return [v.create_multi(index), ]
        return map(
            lambda vv: vv.create_multi(index),
            v
        )


class _Selectors(object):
    def __init__(self):
        self.__selectors = {}
        self.__known_selectors = {}
        self.__load_selectors()

    def __load_selectors(self):
        cfg = common.config.Config()
        if not cfg.exists('/parser/selectors'):
            return
        for d in cfg['/parser/selectors']:
            for f in filter(
                lambda fname: fname.endswith('.json'),
                os.listdir(d)
            ):
                with open(os.path.join(d, f)) as fp:
                    res = Compiler().compile(json.load(fp))
                    self.__add_selectors(res)

    def __add_selectors(self, r):
        for s in r:
            for t in s.get_tags():
                if self.__selectors.has_key(t):
                    sh = self.__selectors[t]
                else:
                    sh = SelectorHub(t)
                    self.__selectors[t] = sh
                sh.add_selector(s)

    def __getitem__(self, index):
        return self.__selectors[index]

    def __iter__(self):
        for v in self.__selectors.values():
            yield v


@singleton
class Preprocessor(_Preprocessor):
    pass


@singleton
class Compiler(_Compiler):
    pass


@singleton
class Selectors(_Selectors):
    pass


def selector(name):
    return Selectors()[name]
