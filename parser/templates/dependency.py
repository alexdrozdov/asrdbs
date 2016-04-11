#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import LinkSpecs


class DependencySpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencySpec, self).__init__('dependency')

    def __call__(self, type_name, master=None):
        if master is None:
            master = [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ]
        return \
            {
                "type": type_name,
                "master": master
            }
