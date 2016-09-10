#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import SelectorSpecs


class SelectorSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(SelectorSpec, self).__init__('selector')

    def __call__(self, body, *args):
        name = args[0]
        body['selector'] = SelectorSpecs().Selector(name)


class TemplateSelector(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'selector',
            namespace='specs',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args):
        name = body.pop('@selector')
        body['selector'] = SelectorSpecs().Selector(name)
