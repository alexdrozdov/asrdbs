#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates


class Named(object):
    def __init__(self, constructors, reusable=False):
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
                clsdef_obj[1].get_name(): clsdef_obj[0] for clsdef_obj in map(
                    lambda clsdef: (clsdef, clsdef()),
                    constructors
                )
            }

    def __getitem__(self, name):
        if self.__reusable:
            return self.__objs[name]
        else:
            return self.__objs[name]()

tmpl = None


def load_named_instances():
    global tmpl
    tmpl = Named(parser.templates.load_templates())


class SequentialFuncCall(object):
    def __init__(self, func_list):
        self.__func_list = func_list

    def __call__(self, *args, **kwargs):
        res = self.__func_list[0](*args, **kwargs)
        for f in self.__func_list[1:]:
            res = f(res)
        return res


def template(name, *args):
    if not args:
        return tmpl[name]
    l = [name, ] + list(args)
    l.reverse()
    return SequentialFuncCall(
        map(
            lambda n: tmpl[n],
            l
        )
    )
