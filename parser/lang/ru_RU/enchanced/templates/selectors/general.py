#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.sdefs import PosSpecs, WordSpecs, RelationsSpecs


class PosSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(PosSpec, self).__init__('pos', namespace='selectors')

    def __call__(self, body):
        names = body.pop('@pos')
        if not isinstance(names, list):
            names = [names, ]
        body['pos'] = [PosSpecs().IsPos(names), ]


class WordSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(WordSpec, self).__init__('word', namespace='selectors')

    def __call__(self, body):
        words = body.pop('@word')
        if not isinstance(words, list):
            words = [words, ]
        body['word'] = [WordSpecs().IsWord(words), ]


class AnimationSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(AnimationSpec, self).__init__('animation', namespace='selectors')

    def __call__(self, body):
        qualifier = str(body.pop('@animation'))
        inv = qualifier.startswith('!') or qualifier.startswith('in')
        if inv:
            qualifier = qualifier.replace('!', '').replace('in', '')
        assert qualifier == 'animated'
        body['animation'] = [PosSpecs().IsAnimated() if not inv else PosSpecs().IsInanimated(), ]


class SelfSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(SelfSpec, self).__init__('self', namespace='selectors')

    def __call__(self, body):
        body['0'] = body.pop('@self')


class OtherSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(OtherSpec, self).__init__('other', namespace='selectors')

    def __call__(self, body):
        body['1'] = body.pop('@other')


class EqualPropsSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(EqualPropsSpec, self).__init__('equal-properties', namespace='selectors')

    def __call__(self, body):
        ep = body.pop('@equal-properties')
        body['equal-properties'] = map(
            lambda (other_indx, s): RelationsSpecs().EqualProps(int(other_indx), s),
            ep.items()
        )


class PositionSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(PositionSpec, self).__init__('position', namespace='selectors')

    def __call__(self, body):
        pr = body.pop('@position')
        body['position'] = map(
            lambda (other_indx, s): RelationsSpecs().Position(int(other_indx), s),
            pr.items()
        )


class LinkSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(LinkSpec, self).__init__('link', namespace='selectors')

    def __call__(self, body):
        body['link'] = body.pop('@link')
