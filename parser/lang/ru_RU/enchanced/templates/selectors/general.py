#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.sdefs import PosSpecs, RelationsSpecs


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


class SelfSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(SelfSpec, self).__init__('self', namespace='selectors')

    def __call__(self, body, **sp):
        assert isinstance(sp, dict)
        body["self"] = sp


class OtherSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(OtherSpec, self).__init__('other', namespace='selectors')

    def __call__(self, body, **sp):
        assert isinstance(sp, dict)
        body["other"] = sp


class EqualPropsSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(EqualPropsSpec, self).__init__('equal-properties', namespace='selectors')

    def __call__(self, body, sp):
        if not isinstance(sp, list):
            sp = [sp, ]
        body["equal-properties"] = [RelationsSpecs().EqualProps(sp), ]


class PositionSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(PositionSpec, self).__init__('position', namespace='selectors')

    def __call__(self, body, sp):
        body["position"] = [RelationsSpecs().Position(sp), ]


class LinkSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(LinkSpec, self).__init__('link', namespace='selectors')

    def __call__(self, body, **sp):
        assert isinstance(sp, dict)
        body["link"] = sp
