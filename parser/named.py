#!/usr/bin/env python
# -*- #coding: utf8 -*-


import common.config
from common.singleton import singleton


class Named(object):
    def __init__(self, constructors, reusable=False, def_namespace=None):
        self.__reusable = reusable
        if self.__reusable:
            self.__objs = {
                obj.get_name(): obj for obj in map(
                    lambda clsdef: clsdef(),
                    constructors
                )
            }
        else:
            self.__objs = {
                (clsdef_obj[1].get_name(), clsdef_obj[1].get_namespace()):
                    clsdef_obj[0] for clsdef_obj in map(
                        lambda clsdef: (clsdef, clsdef()),
                        constructors
                    )
            }

    def __getitem__(self, name):
        if self.__reusable:
            return self.__objs[name]
        else:
            if self.__objs.has_key(name):
                return self.__objs[name]()
            if self.__objs.has_key((name[0], None)):
                return self.__objs[(name[0], None)]
            raise KeyError('Key {0}:{1} not found'.format(name[1], name[0]))


class _Templates(Named):
    def __init__(self):
        super(_Templates, self).__init__(self.__load_templates())

    def __load_templates(self):
        cfg = common.config.Config()
        return reduce(
            lambda x, y: x + y,
            map(
                lambda tmpl_dir: self.__load_module(tmpl_dir).load_templates(),
                cfg['/parser/templates']
            ),
            []
        )

    def __load_module(self, path):
        parts = map(
            lambda p: str(p),
            path.split('/')
        )
        root = parts[0]
        parts = parts[1:]
        path = root
        obj = __import__(root, globals(), locals(), root)
        for p in parts:
            path += '.' + p
            obj = __import__(str(path), globals(), locals(), str(path))
        return obj


@singleton
class Templates(_Templates):
    pass


class SequentialFuncCall(object):
    def __init__(self, func_list):
        self.__func_list = func_list

    def __call__(self, *args, **kwargs):
        res = self.__func_list[0](*args, **kwargs)
        for f in self.__func_list[1:]:
            res = f(res)
        return res


def template(name, *args, **kwargs):
    if kwargs.has_key('namespace'):
        namespace = kwargs['namespace']
    else:
        namespace = None

    if not args:
        return Templates()[name, namespace]
    l = [name, ] + list(args)
    l.reverse()
    return SequentialFuncCall(
        map(
            lambda n: Templates()[n, namespace],
            l
        )
    )
