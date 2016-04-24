#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import RefersToSpecs


class DependencySpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencySpec, self).__init__('refers-to')

    def __call__(self, master=None):
        if master is None:
            master = "$LOCAL_SPEC_ANCHOR"
        return [RefersToSpecs().AttachTo(master), ]
