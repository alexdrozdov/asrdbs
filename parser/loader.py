#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import re
import json
import copy
import parser.named
import common.config
import parser.lang.common
from common.singleton import singleton
from parser.lang.defs import RequiredSpecs, FsmSpecs


class _Preprocessor(object):
    def __init__(self):
        pass

    def preprocess(self, spec):
        spec = copy.deepcopy(spec)

        while True:
            try:
                print(type(spec))
                for d, k, v in self.__iterspec(spec):
                    if k[0] == '@':
                        self.__handle_tmpl(d, k, v)
                break
            except parser.templates.common.ErrorRerun:
                print('caught rerun')
                continue

        return spec

    def __handle_tmpl(self, d, k, v):
        k = k.replace('@', '')
        tmpl = parser.named.template(k, namespace='specs')
        tmpl(d)

    def __handle_val_tmpl(self, v):
        return v

    def __iterspec(self, rule, exclude=None):
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude, ]
        keys = list(filter(
            lambda k: k not in exclude,
            list(rule.keys()),
        ))

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


class _PreCompiler(object):
    def __init__(self):
        pass

    def compile(self, js):
        js = Preprocessor().preprocess(js)

        entries = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            }
        ] + js['entries'] + [
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            }
        ]
        return [parser.lang.common.SequenceSpec(
            name=js['name'],
            spec=entries
        ), ]


class _Specs(object):
    def __init__(self):
        self.__specs = {}
        self.__load_specs()

    def __load_specs(self):
        cfg = common.config.Config()
        if not cfg.exists('/parser/specdefs'):
            return
        for d in cfg['/parser/specdefs']:
            d = 'parser/lang/' + d
            for f in [fname for fname in os.listdir(d) if fname.endswith('.json')]:
                path = os.path.join(d, f)
                if path.endswith('.multi.json'):
                    self.__load_multi(path)
                else:
                    self.__load_single(path)

    def __load_single(self, path):
        with open(path) as fp:
            res = PreCompiler().compile(json.load(fp))
            self.__add_specs(res)

    def __load_multi(self, path):
        with open(path) as fp:
            data = fp.read()
            for s in [_f for _f in re.split('^//.*\n', data, flags=re.MULTILINE) if _f]:
                res = PreCompiler().compile(json.loads(s))
                self.__add_specs(res)

    def __add_specs(self, specs):
        for s in specs:
            assert s.get_name() not in self.__specs
            self.__specs[s.get_name()] = s

    def __getitem__(self, index):
        return self.__specs[index]

    def __iter__(self):
        for v in self.__specs.values():
            yield v


@singleton
class PreCompiler(_PreCompiler):
    pass


@singleton
class Preprocessor(_Preprocessor):
    pass


@singleton
class Specs(_Specs):
    pass


def specs(name):
    return Specs()[name]
