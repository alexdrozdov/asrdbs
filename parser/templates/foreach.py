#!/usr/bin/env python
# -*- #coding: utf8 -*-


import copy
import parser.templates.common


class ForEachSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'foreach',
            namespace=None,
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        prototype = body.pop('@foreach')
        if 'entries' in body:
            lst = body['entries']
        elif 'uniq-items' in body:
            lst = body['uniq-items']
        else:
            raise ValueError("neither entries nor uniq-items found")

        for i, item in enumerate(lst):
            p = copy.deepcopy(prototype)
            for k, v in list(p.items()):
                if k in item and isinstance(p[k], list):
                    item[k].extend(v)
                else:
                    item[k] = v
            item["@id"] = "phr-{0}".format(i)
        raise parser.templates.common.ErrorRerun()
