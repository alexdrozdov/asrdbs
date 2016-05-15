#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common


class IncludeSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(IncludeSpec, self).__init__('include')

    def __call__(self, spec_name, is_static=False):
        return \
            {
                "spec": spec_name,
                "static-only": is_static,
            }


class IncludesSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(IncludesSpec, self).__init__('includes')

    def __call__(self, body, name, is_static=False):
        body['include'] = {
            "spec": name,
            "static-only": is_static,
        }
