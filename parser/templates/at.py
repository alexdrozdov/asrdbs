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
        tmpl_name = k.replace('@', '')
        tmpl = parser.named.template(tmpl_name)
        if tmpl.args_mode() == \
                parser.templates.common.SpecTemplate.ARGS_MODE_UNROLL:
            v = d.pop(k)
            if isinstance(v, dict):
                tmpl(d, **v)
            elif isinstance(v, (list, tuple)):
                tmpl(d, *v)
            else:
                tmpl(d, v)
        else:
            tmpl(d)

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
        if 'entries' in d:
            self.__iter_list(d['entries'])
        if 'uniq-items' in d:
            self.__iter_list(d['uniq-items'])

    def __call__(self, d):
        if isinstance(d, dict):
            self.__handle_dict(d)
        else:
            self.__iter_list(d)
        return d
