#!/usr/bin/env python
# -*- #coding: utf8 -*-


import json


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


class AppConfig(object):
    def __init__(self, filename=None, obj=None):
        if filename is not None:
            assert obj is None
            with open(filename) as f:
                obj = json.load(f)
        self.__obj = obj

    def register_unit(self, name, cfg=None):
        if name in self.__obj:
            return
        if cfg is None:
            cfg = {}
            self.__obj[name] = cfg

    def exists(self, path):
        return self.__xpath_get(path) is not None

    def __xpath_get(self, path):
        elem = self.__obj
        try:
            for x in path.strip("/").split("/"):
                try:
                    x = int(x)
                    elem = elem[x]
                except ValueError:
                    elem = elem.get(x)
        except:
            return None
        return elem

    def __xpath_set(self, path, value):
        elem = self.__obj
        path = path.strip("/").split("/")
        base_path = path[0:-1]
        last_name = path[-1]
        try:
            for x in base_path:
                try:
                    x = int(x)
                    elem = elem[x]
                except ValueError:
                    elem = elem.get(x)
            try:
                x = int(last_name)
                elem[x] = value
            except ValueError:
                elem[last_name] = value
        except:
            pass

    def __getitem__(self, i):
        return self.__xpath_get(i)

    def __setitem__(self, k, v):
        self.__xpath_set(k, v)


@singleton
class Config(AppConfig):
    pass
