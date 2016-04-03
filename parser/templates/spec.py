#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import RequiredSpecs, FsmSpecs


class TemplateSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateSpec, self).__init__('spec')

    def __call__(self, d):
        if isinstance(d, dict):
            d = [d, ]
        return \
            [{
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            }] + \
            d + \
            [{
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            }]
