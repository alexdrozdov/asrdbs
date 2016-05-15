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
            for k, v in bb.items():
                body[k] = v

    def __get_base(self, base):
        bases = {
            'basic-adj': {
                "pos_type": [PosSpecs().IsAdjective(), ]
            },
            'basic-adv': {
                "pos_type": [PosSpecs().IsAdverb(), ]
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
        }
        # b = {
        #     "selector": [
        #         {
        #             "test": [
        #                 {"pos_type": [PosSpecs().IsAdjective(), ]},
        #             ],
        #             "apply": [
        #             ]
        #         }
        #     ]
        # }

        return copy.deepcopy(bases[base])
