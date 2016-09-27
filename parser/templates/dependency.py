#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import DependencySpecs


class DependencySpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencySpec, self).__init__('dependency')

    def __call__(self, dependency_class, master=None):
        if master is None:
            master = [DependencySpecs().DependencyOf("$LOCAL_SPEC_ANCHOR", dependency_class), ]
        else:
            master = [DependencySpecs().DependencyOf(master, dependency_class), ]
        return master


class DependencyOfSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencyOfSpec, self).__init__('dependency-of')

    def __call__(self, body, dependency_class, master=None):
        if master is None:
            master = [DependencySpecs().DependencyOf("$LOCAL_SPEC_ANCHOR", dependency_class), ]
        else:
            master = [DependencySpecs().DependencyOf(master, dependency_class), ]
        body['dependency-of'] = master


class DependencyOfSpec_js(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'dependency-of',
            namespace='specs',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        master = None
        dp_info = body.pop('@dependency-of')
        dp_id = dp_info[0]
        if 2 <= len(dp_info):
            master = dp_info[1]
        if master is None:
            master = [DependencySpecs().DependencyOf("$LOCAL_SPEC_ANCHOR", dp_id), ]
        else:
            master = [DependencySpecs().DependencyOf(master, dp_id), ]
        body['dependency-of'] = master
