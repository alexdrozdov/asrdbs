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
        if self.__obj.has_key(name):
            return
        if cfg is None:
            cfg = {}
            self.__obj[name] = cfg

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

    def __getitem__(self, i):
        return self.__xpath_get(i)


@singleton
class Config(AppConfig):
    pass
