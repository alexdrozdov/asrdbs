#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.named
import parser.templates.common


class TemplateAt(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateAt, self).__init__('@')

    def __iter_list(self, l):
        for e in l:
            if isinstance(e, dict):
                self.__handle_dict(e)
            else:
                self.__iter_list(e)

    def __handle_key_tmpl(self, d, k):
        v = d.pop(k)
        k = k.replace('@', '')
        tmpl = parser.named.template(k)
        if isinstance(v, dict):
            tmpl(d, **v)
        elif isinstance(v, (list, tuple)):
            tmpl(d, *v)
        else:
            tmpl(d, v)

    def __handle_dict(self, d):
        modified = False
        first_run = True
        while modified or first_run:
            modified = False
            first_run = False
            self.__descend_dict(d)
            for k in d.keys():
                if k[0] == '@':
                    self.__handle_key_tmpl(d, k)
                    modified = True

    def __descend_dict(self, d):
        if d.has_key('entries'):
            self.__iter_list(d['entries'])
        if d.has_key('uniq-items'):
            self.__iter_list(d['uniq-items'])

    def __call__(self, d):
        if isinstance(d, dict):
            self.__handle_dict(d)
        else:
            self.__iter_list(d)
        return d
