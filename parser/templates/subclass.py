#!/usr/bin/env python
# -*- #coding: utf8 -*-


import re
import copy
import parser.templates.common


class TemplateSubclass(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'subclass',
            namespace=None,
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        superclass_spec_name = body.pop('@subclass')
        rewrite = body.pop('rewrite')
        scope = kwargs['scope']
        spec = scope.spec(superclass_spec_name, original_json=True)
        spec = copy.deepcopy(spec)

        self.__rewrite_spec(spec, rewrite)
        self.__merge_spec(body, spec)
        raise parser.templates.common.ErrorRerun()

    def __rewrite_spec(self, spec, rewrite):
        for rule in rewrite:
            find = rule['find']
            extend = rule['extend']
            for e in self.__iterall(spec):
                if self.__rule_matched(e, find):
                    self.__rule_apply(e, extend)

    def __merge_spec(self, body, spec):
        for k, v in spec.items():
            if k == 'name':
                continue
            body[k] = v

    def __iterall(self, l):
        if 'entries' in l:
            for ee in self.__iterall(l['entries']):
                yield ee
        if 'uniq-items' in l:
            for ee in self.__iterall(l['uniq-items']):
                yield ee

    def __rule_matched(self, e, r):
        for k, v in list(r.items()):
            if k not in e and '@' + k not in e:
                return False
            if '@' + k in e:
                k = '@' + k
            if re.match(v, e[k]) is None:
                return False
        return True

    def __rule_apply(self, e, extend):
        for k, v in list(extend.items()):
            e[k] = v
