#!/usr/bin/env python
# -*- #coding: utf8 -*-


import copy
import parser.templates.common
from parser.lang.defs import PosSpecs, RepeatableSpecs, AnchorSpecs


class DependencySpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencySpec, self).__init__('inherit')

    def __call__(self, body, *args):
        for base in args:
            bb = self.__get_base(base)
            for k, v in list(bb.items()):
                self.__extend_attr(body, k, v)

    def __extend_attr(self, body, attr, val):
        if not isinstance(val, list):
            body[attr] = val
            return

        if attr in body:
            v = body[attr]
            if not isinstance(v, list):
                v = [v, ]
        else:
            v = []
        v.extend(val)
        body[attr] = v

    def __get_base(self, base):
        bases = {
            'basic-adj': {
                "pos_type": [PosSpecs().IsAdjective(), ]
            },
            'basic-adv': {
                "pos_type": [PosSpecs().IsAdverb(), ]
            },
            'basic-noun': {
                "pos_type": [PosSpecs().IsNoun(), ]
            },
            'union': {
                "pos_type": [PosSpecs().IsUnion(), ]
            },
            'comma': {
                "pos_type": [PosSpecs().IsComma(), ]
            },
            'once': {
                "repeatable": RepeatableSpecs().Once(),
            },
            'any': {
                "repeatable": RepeatableSpecs().Any(),
            },
            'anchor': {
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            '#object': {
                "@selector": "#object",
            }
        }

        return copy.deepcopy(bases[base])
