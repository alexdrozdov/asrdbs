#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import DependencySpecs


class DependencySpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencySpec, self).__init__('dependency')

    def __call__(self, dependency_class, master=None):
        if master is None:
            master = [DependencySpecs().DependencyOf("$LOCAL_SPEC_ANCHOR"), ]
        else:
            master = [DependencySpecs().DependencyOf(master), ]
        return master


class DependencyOfSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencyOfSpec, self).__init__('dependency-of')

    def __call__(self, body, dependency_class, master=None):
        if master is None:
            master = [DependencySpecs().DependencyOf("$LOCAL_SPEC_ANCHOR"), ]
        else:
            master = [DependencySpecs().DependencyOf(master), ]
        body['dependency-of'] = master
