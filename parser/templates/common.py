#!/usr/bin/env python
# -*- #coding: utf8 -*-


class SpecTemplate(object):
    def __init__(self, name):
        self.__name = name

    def get_name(self):
        return self.__name
