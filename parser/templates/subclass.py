#!/usr/bin/env python
# -*- #coding: utf8 -*-


import re
import parser.templates.common


class TemplateSubclass(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateSubclass, self).__init__('subclass')

    def __call__(self, base, rewrite=None):
        spec = base().get_spec()
        if rewrite is None:
            return spec

        for rule in rewrite:
            find = rule['find']
            extend = rule['extend']
            for e in self.__iterall(spec):
                if self.__rule_matched(e, find):
                    self.__rule_apply(e, extend)

        return spec

    def __iterall(self, l):
        for e in l:
            if e.has_key('entries'):
                for ee in self.__iterall(e['entries']):
                    yield ee
            if e.has_key('uniq-items'):
                for ee in self.__iterall(e['uniq-items']):
                    yield ee
            yield e

    def __rule_matched(self, e, r):
        for k, v in r.items():
            if not e.has_key(k):
                return False
            if re.match(v, e[k]) is None:
                return False
        return True

    def __rule_apply(self, e, extend):
        for k, v in extend.items():
            e[k] = v
