#!/usr/bin/env python
# -*- #coding: utf8 -*-


import copy
import parser.templates.common


class ForEachSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(ForEachSpec, self).__init__('foreach')

    def __call__(self, prototype, items):
        r = []
        for i, item in enumerate(items):
            p = copy.deepcopy(prototype)
            for k, v in item.items():
                if p.has_key(k) and isinstance(p[k], list):
                    p[k].extend(v)
                else:
                    p[k] = v
            p["id"] = "$PARENT::phr-{0}".format(i)
            r.append(p)
        return r
