#!/usr/bin/env python
# -*- #coding: utf8 -*-


class SpecTemplate(object):
    def __init__(self, name, namespace=None):
        self.__name = name
        self.__namespace = namespace

    def get_name(self):
        return self.__name

    def get_namespace(self):
        return self.__namespace
