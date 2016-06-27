#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import copy
import json
import uuid
import parser.named
import common.config
from argparse import Namespace as ns
from common.singleton import singleton


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
        self.__tags = tags
        self.__clarifies = clarifies
        self.__rules = rules

    def get_tags(self):
        return self.__tags

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
            form.add_tag(t)

    def __call__(self, *argc, **argv):
        test_only = argv['test_only'] if argv.has_key('test_only') else False
        return self.__apply(argc[0], test_only=test_only)

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
    def __init__(self, tags, clarifies, rules, link_attrs, reorder=None):
        assert None not in tags
        assert isinstance(clarifies, ns) and \
            None not in clarifies.s and \
            None not in clarifies.o

        assert reorder is not None
        self.__tags = tags
        self.__clarifies = clarifies
        self.__rules = rules
        self.__link_attrs = link_attrs
        self.__reorder = reorder

    def get_tags(self):
        return self.__tags

    def apply(self, form, other_form):
        return self.__apply(form, other_form, test_only=False)

    def test(self, form, other_form):
        return self.__apply(form, other_form, test_only=True)

    def __failure(self):
        return SelectorRes(False)

    def __apply(self, s_form, o_form, test_only=False):
        form, other_form = self.__reorder((s_form, o_form))

        res = SelectorRes(True)
        for c in self.__clarifies.s:
            res = res and self.__check_clarify(s_form, o_form, c)
            if not res:
                return self.__failure()

        for c in self.__clarifies.o:
            res = res and self.__check_clarify(o_form, s_form, c)
            if not res:
                return self.__failure()

        for r in self.__rules:
            if not r.match(form, other_form):
                return self.__failure()
        self.__set_tags(s_form)

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

    def __check_clarify(self, s_form, o_form, tag):
        if s_form.has_tag(tag):
            return SelectorRes(True)
        selector = Selectors()[tag]
        return selector(s_form, o_form)

    def __set_tags(self, form):
        for t in self.__tags:
            form.add_tag(t)

    def __call__(self, *argc, **argv):
        test_only = argv['test_only'] if argv.has_key('test_only') else False
        return self.__apply(argc[0], argc[1], test_only=test_only)

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

    def get_tag(self):
        return self.__tag

    def add_selector(self, selector):
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

    def apply(self, *argc, **argv):
        return self.__apply(*argc, test_only=False)

    def test(self, *argc, **argv):
        return self.__apply(*argc, test_only=True)

    def __call__(self, *argc, **argv):
        return self.__apply(*argc, **argv)

    def __repr__(self):
        return "SelectorHub({0})".format(self.get_tag())

    def __str__(self):
        return "SelectorHub({0})".format(self.get_tag())


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
        v = d.pop(k)
        k = k.replace('@', '')
        tmpl = parser.named.template(k, namespace='selectors')
        if isinstance(v, dict):
            tmpl(d, **v)
        elif isinstance(v, (list, tuple)):
            tmpl(d, *v)
        else:
            tmpl(d, v)

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
            return self.__multi(js[u'multi'], clarifies, base_tags)
        raise KeyError('neither selector nor multi key found in selector spec')

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
                lambda (r, v): self.__mk_rule(r, v),
                self.__rules(js)
            ),
            []
        )

        if tags:
            selectors.append(Selector(tags + base_tags, clarifies, rules))

        for c in self.__get_property_list(js, u'clarify'):
            selectors.extend(self.__compile(c, tags, base_tags))

        return selectors

    def __compile_multi(self, js, clarifies, base_tags, reorder=None):
        assert base_tags is None or None not in base_tags
        selectors = []

        tags = self.__get_property_list(js, u'tag', '#' + str(uuid.uuid1()))
        assert None not in tags
        base_tags = self.__as_list(base_tags, none_is_empty=True) +\
            self.__get_property_list(js, u'tag-base')
        assert None not in base_tags
        clarifies = self.__as_list(clarifies)

        clarifies.extend(self.__get_property_list(js, u'clarifies'))
        rules = reduce(
            lambda x, y: x + y,
            map(
                lambda (r, v): self.__mk_rule(r, v),
                self.__rules(js)
            ),
            []
        )

        link_attrs = js[u'link'] if u'link' in js else {}

        if tags:
            selectors.append(
                MultiSelector(
                    tags + base_tags,
                    ns(s=clarifies, o=[]),
                    rules,
                    link_attrs,
                    reorder
                )
            )

        for c in self.__get_property_list(js, u'clarify'):
            selectors.extend(
                self.__compile_multi(
                    c,
                    tags,
                    base_tags,
                    reorder=reorder
                ).full_list
            )

        return ns(
            primary=selectors[0:1],
            full_list=selectors
        )

    def __compile_self(self, js, clarifies, base_tags):
        return self.__compile_multi(
            js,
            clarifies,
            base_tags,
            reorder=lambda (x, y): (x, y)
        )

    def __compile_other(self, js, clarifies, base_tags):
        return self.__compile_multi(
            js,
            clarifies,
            base_tags,
            reorder=lambda (x, y): (y, x)
        )

    def __multi(self, js, clarifies, base_tags):
        assert base_tags is None or None not in base_tags

        base_tags = self.__as_list(base_tags, none_is_empty=True) +\
            self.__get_property_list(js, u'tag-base')
        assert None not in base_tags
        assert None not in clarifies

        s_res = self.__compile_self(js['self'], clarifies, [])
        o_res = self.__compile_other(js['other'], clarifies, [])
        s = MultiSelector(
            base_tags,
            ns(
                s=self.__tags(s_res.primary),
                o=self.__tags(o_res.primary)
            ),
            [],
            {},
            reorder=lambda (x, y): (x, y)
        )
        return [s, ] + s_res.full_list + o_res.full_list

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
            'pos_type', 'case', 'animation',
            'position', 'equal-properties'
        ]
        return map(
            lambda k: (k, js[k]),
            filter(
                lambda k: k in known_rules,
                js.keys()
            )
        )

    def __mk_rule(self, k, v):
        if not isinstance(v, list):
            return [v.create(), ]
        return map(
            lambda vv: vv.create(),
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
