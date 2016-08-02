#!/usr/bin/env python
# -*- #coding: utf8 -*-


class SpecTemplate(object):

    ARGS_MODE_UNROLL = 0
    ARGS_MODE_NATIVE = 1

    def __init__(self, name, namespace=None, args_mode=None):
        self.__name = name
        self.__namespace = namespace
        self.__args_mode = args_mode if args_mode is not None \
            else SpecTemplate.ARGS_MODE_UNROLL

    def get_name(self):
        return self.__name

    def get_namespace(self):
        return self.__namespace

    def args_mode(self):
        return self.__args_mode
