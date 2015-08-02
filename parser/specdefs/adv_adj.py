#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class AdvAdjSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adj-adv')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "adv",
                "pos_type": [PosSpecs().IsAdverb(), ],
                "position": [PositionSpecs().IsBefore("adj"), ],
                "master-slave": [LinkSpecs().IsSlave("adj"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("adj"), ],
                "add-to-seq": True
            },
            {
                "required": RequiredSpecs().IsOptional(),
                "id": "adv+",
                "pos_type": [PosSpecs().IsAdverb(), ],
                "position": [PositionSpecs().IsBefore("adj"), ],
                "master-slave": [LinkSpecs().IsSlave("adj"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("adj"), ],
                "repeatable": True,
                "add-to-seq": True
            },
            {
                "id": "adj",
                "required": RequiredSpecs().IsNecessary(),
                "pos_type": [PosSpecs().IsAdjective(), ],
                "add-to-seq": True
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
