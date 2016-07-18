#!/usr/bin/env python
# -*- #coding: utf8 -*-


class IfModified(object):
    def __init__(self, obj, revision_cb):
        self.__obj = obj
        self.__revision_cb = revision_cb
        self.__revision = self.__revision_cb(self.__obj)

    def modified(self):
        return self.__revision == self.__revision_cb(self.__obj)

    def refresh(self):
        self.__revision = self.__revision_cb(self.__obj)

    def get(self):
        return self.__obj

    def __getattr__(self, name):
        return self.__obj.__getattribute__(name)
