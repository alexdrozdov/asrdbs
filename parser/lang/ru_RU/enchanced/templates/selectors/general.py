#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.sdefs import PosSpecs


class PosSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(PosSpec, self).__init__('pos', namespace='selectors')

    def __call__(self, body, names):
        if not isinstance(names, list):
            names = [names, ]
        body["pos_type"] = [PosSpecs().IsPos(names), ]


class AnimationSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(AnimationSpec, self).__init__('animation', namespace='selectors')

    def __call__(self, body, qualifier):
        qualifier = str(qualifier)
        inv = qualifier.startswith('!') or qualifier.startswith('in')
        if inv:
            qualifier = qualifier.replace('!', '').replace('in', '')
        assert qualifier == 'animated'
        body["animation"] = [PosSpecs().IsAnimated() if not inv else PosSpecs().IsInanimated(), ]
