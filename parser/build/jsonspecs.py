#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import copy
import common.config
import common.multijson
import parser.spare.rules
import parser.spare.atjson
from common.singleton import singleton
from parser.lang.base.rules.defs import RequiredSpecs, FsmSpecs


class PreprocessScope(object):
    def __init__(self):
        self.__specs = {}

    def add_specs(self, compiled_specs, source):
        for s in compiled_specs:
            self.__specs[s.get_name()] = {'spec': s, 'source': source}

    def spec(self, name, original_json=True):
        return self.__specs[name]['source']


class _Preprocessor(parser.spare.atjson.AtJson):
    def __init__(self):
        super().__init__(namespace='specs')


class _PreCompiler(object):
    def __init__(self):
        pass

    def compile(self, js, scope):
        js = Preprocessor().preprocess(js, scope)

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
        return [parser.spare.rules.SequenceSpec(
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
            self.__loaddir(d)

    def __loaddir(self, dirname):
        for f in os.listdir(dirname):
            fullname = os.path.join(dirname, f)
            if os.path.isdir(fullname):
                self.__loaddir(fullname)
            elif os.path.isfile(fullname) and fullname.endswith('.json'):
                self.__load_file(fullname)

    def __load_file(self, filename):
        scope = PreprocessScope()
        mj = common.multijson.MultiJsonFile(filename)
        for j in mj.dicts():
            res = PreCompiler().compile(copy.deepcopy(j), scope=scope)
            scope.add_specs(res, source=copy.deepcopy(j))
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
