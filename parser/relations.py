#!/usr/bin/env python
# -*- #coding: utf8 -*-


from common.singleton import singleton
from argparse import Namespace as ns


class RelTerm(object):
    def __init__(self, desc):
        self.__namespace = desc.namespace
        self.__name = desc.name
        self.__description = desc.description
        self.__relations = {}

    def add_relation(self, other_term, relation):
        self.__relations[relation] = [other_term, ]


class _Relations(object):
    def __init__(self):
        self.__items = {}

    def create_term(self, term):
        assert isinstance(term, ns)
        if term.namespace not in self.__items:
            self.__items[term.namespace] = {}
        self.__items[term.namespace][term.name] = RelTerm(term)

    def add_relation(self, terms, relation):
        self.get_term(terms[0]).add_relation(terms[1], relation)


@singleton
class Relations(_Relations):
    pass
