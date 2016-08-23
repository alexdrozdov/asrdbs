#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import re
import json
import copy
import common.config
from common.singleton import singleton

#         for t in props.default().tags():
#             if not self.has_tag(t) and not self.restricted(t):
#                 self.__layers[layer][t] = True
#         self.__copy_expected_properties(layer, props.default.properties())
#         self.__copy_disabled_properties(layer, props.disabled())


class PropSetGroup(object):
    def __init__(self, d):
        self.__d = d

    def tags(self):
        for k in self.__d:
            if k.startswith('#'):
                yield k

    def properties(self):
        for k, v in self.__d.items():
            if not k.startswith('#'):
                yield k, v


class PropSet(object):
    def __init__(self, tag, props):
        self.__tag = tag
        self.__props = copy.deepcopy(props)
        self.__default = PropSetGroup(self.__props['default'])
        self.__disabled = self.__props['disabled']

    def tag(self):
        return self.__tag

    def default(self):
        return self.__default

    def disabled(self):
        return self.__disabled


class _Compiler(object):
    def __init__(self):
        pass

    def compile(self, js):
        if js['type'] != 'obj-props':
            return []
        p = {}
        if 'default' in js:
            p['default'] = js['default']
        if 'disabled' in js:
            p['disabled'] = js['disabled']
        return [PropSet(js['tag'], p), ]


class _Properties(object):
    def __init__(self):
        self.__props = {}
        self.__load_props()

    def __load_props(self):
        cfg = common.config.Config()
        if not cfg.exists('/parser/props'):
            return
        for d in cfg['/parser/props']:
            for f in [fname for fname in os.listdir(d) if fname.endswith('.json')]:
                path = os.path.join(d, f)
                if path.endswith('.multi.json'):
                    self.__load_multi(path)
                else:
                    self.__load_single(path)

    def __load_single(self, path):
        with open(path) as fp:
            res = Compiler().compile(json.load(fp))
            self.__add_props(res)

    def __load_multi(self, path):
        with open(path) as fp:
            data = fp.read()
            for s in [_f for _f in re.split('^//.*\n', data, flags=re.MULTILINE) if _f]:
                res = Compiler().compile(json.loads(s))
                self.__add_props(res)

    def __add_props(self, r):
        for ps in r:
            if ps.tag() in self.__props:
                self.__props[ps.tag()] += ps
            else:
                self.__props[ps.tag()] = ps

    def __getitem__(self, index):
        return self.__props.get(index, None)

    def __iter__(self):
        for v in list(self.__props.values()):
            yield v


@singleton
class Compiler(_Compiler):
    pass


@singleton
class Properties(_Properties):
    pass


def properties(tag):
    return Properties()[tag]
