#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import copy
import uuid
import common.config
import common.c3
import common.multijson
from common.singleton import singleton


class PropSetGroup(object):
    def __init__(self, d):
        self.__d = d

    @classmethod
    def empty(cls):
        return PropSetGroup({})

    @classmethod
    def from_propsetgroup(cls, psg):
        return PropSetGroup(copy.deepcopy(psg.__d))

    def tags(self):
        for k in self.__d:
            if k.startswith('#'):
                yield k

    def properties(self):
        for k, v in self.__d.items():
            if not k.startswith('#'):
                yield k, v

    def __merge_dict(self, d):
        keys1 = self.__d.keys()
        keys2 = d.keys()
        new_keys = set(keys2) - set(keys1)
        for k in new_keys:
            self.__d[k] = copy.deepcopy(d[k])

    def __iadd__(self, other):
        if other is None:
            return self
        self.__merge_dict(other.__d)
        return self

    def __add__(self, other):
        if other is None:
            return PropSetGroup.from_propset(self)
        a = PropSetGroup.from_propsetgroup(self)
        a += other
        return a


class PropSet(object):
    def __init__(self, tag, props, superclasses=None):
        self.__tag = tag
        self.__props = copy.deepcopy(props)
        self.__default = PropSetGroup(self.__props['default'])
        self.__disabled = self.__props['disabled']
        if superclasses is None:
            superclasses = []
        self.__superclasses = copy.deepcopy(superclasses)

    @classmethod
    def empty(cls, tag):
        return PropSet(
            tag,
            {
                'default': {},
                'disabled': {},
            }
        )

    @classmethod
    def from_propset(cls, ps):
        return PropSet(
            ps.tag(),
            ps.__props,
            ps.__superclasses
        )

    def tag(self):
        return self.__tag

    def default(self):
        return self.__default

    def disabled(self):
        return self.__disabled

    def superclasses(self):
        return self.__superclasses

    def __merge_disabled(self, other):
        my_keys = self.__disabled.keys()
        other_keys = other.keys()
        new_keys = set(other_keys) - set(my_keys)
        conflicts = set(other_keys) & set(my_keys)
        for k in new_keys:
            self.__disabled[k] = copy.deepcopy(other[k])
        for k in conflicts:
            self.__merge_dict(self.__disabled[k], other[k])

    def __merge_dict(self, d1, d2):
        keys1 = d1.keys()
        keys2 = d2.keys()
        new_keys = set(keys2) - set(keys1)
        for k in new_keys:
            d1[k] = copy.deepcopy(d2[k])

    def __iadd__(self, other):
        if other is None:
            return self
        self.__default += other.default()
        self.__merge_disabled(other.disabled())
        self.__superclasses += other.__superclasses
        return self

    def __add__(self, other):
        if other is None:
            return PropSet.from_propset(self)
        a = PropSet.from_propset(self)
        a += other
        return a


class Relation(PropSet):
    def __init__(self, js):
        tag = js['tag'] if 'tag' in js else str(uuid.uuid1())
        super().__init__(
            tag,
            {
                'default': {},
                'disabled': {},
            },
            list(self.__find_superclasses(js))
        )

    def __find_superclasses(self, js):
        known_keys = (kk for kk in ['subtype-off', 'subclass-off'] if kk in js)
        for k in known_keys:
            for v in js[k]:
                yield v


class _Compiler(object):
    def __init__(self):
        pass

    def compile(self, js):
        if js['type'] == 'obj-props':
            p = {}
            if 'default' in js:
                p['default'] = js['default']
            if 'disabled' in js:
                p['disabled'] = js['disabled']
            return [PropSet(js['tag'], p), ]

        if js['type'] == 'relation':
            return [Relation(js), ]
        return []


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
                self.__load_file(os.path.join(d, f))

    def __load_file(self, filename):
        mj = common.multijson.MultiJsonFile(filename)
        for j in mj.dicts():
            res = Compiler().compile(j)
            self.__add_props(res)

    def __add_props(self, r):
        for ps in r:
            if ps.tag() in self.__props:
                self.__props[ps.tag()] += ps
            else:
                self.__props[ps.tag()] = ps

    def get_by_tag(self, index):
        return self.__props.get(index, None)

    def __preload_hierarchy(self, tag, propset):
        d = {tag: propset.superclasses()}
        pending_tags = set(propset.superclasses())
        while pending_tags:
            t = pending_tags.pop()
            if t in d:
                continue
            ps = self.get_by_tag(t)
            if ps is None:
                continue
            d[t] = ps.superclasses()
            pending_tags |= set(
                [tt for tt in ps.superclasses() if tt not in d]
            )
        return d

    def __accumulate_properties(self, tag, order):
        ps = PropSet.empty(tag)
        for t in order:
            ps += self.get_by_tag(t)
        return ps

    def __aggregate_hierarchy(self, tag, propset):
        hierarchy = self.__preload_hierarchy(tag, propset)
        order = common.c3.C3.linearize(hierarchy)
        return self.__accumulate_properties(tag, order)

    def __getitem__(self, index):
        requested = self.get_by_tag(index)
        if requested is None or not requested.superclasses():
            return requested
        return self.__aggregate_hierarchy(index, requested)

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
