#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import copy
import json
import parser.named
import common.config
from common.singleton import singleton
# from argparse import Namespace as ns


class Selector(object):
    def __init__(self, tags, clarifies, rules):
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
            if not self.__check_clarify(form, c):
                return False
        for r in self.__rules:
            if not r.match(form):
                return False
        self.__set_tags(form)
        return True

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


class SelectorHub(object):
    def __init__(self, tag):
        self.__tag = tag
        self.__selectors = []

    def get_tag(self):
        return self.__tag

    def add_selector(self, selector):
        self.__selectors.append(selector)

    def __apply(self, form, test_only=False):
        return reduce(
            lambda x, y: x or y,
            map(
                lambda s: s(form, test_only=test_only),
                self.__selectors
            ),
            False
        )

    def apply(self, form):
        return self.__apply(form, test_only=False)

    def test(self, form):
        return self.__apply(form, test_only=True)

    def __call__(self, *argc, **argv):
        test_only = argv['test_only'] if argv.has_key('test_only') else False
        return self.__apply(argc[0], test_only=test_only)


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
            self.__clarifies = []
        return self.__compile(js[u'selector'], clarifies, base_tags)

    def __compile(self, js, clarifies, base_tags):
        selectors = []

        tags = self.__get_property_list(js, u'tag')
        base_tags = self.__as_list(base_tags) + self.__get_property_list(js, u'tag-base')
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

    def __get_property_list(self, js, name):
        v = []
        if js.has_key(name):
            v = self.__as_list(js[name])
        return v

    def __as_list(self, v):
        if not isinstance(v, list):
            v = [v, ]
        return v

    def __rules(self, js):
        known_rules = ['pos_type', 'case', 'animation']
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
