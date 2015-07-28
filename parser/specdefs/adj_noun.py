#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class AdjNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adj+-noun')
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
                "id": "adj",
                "pos_type": [PosSpecs().IsAdjective(), ],
                "position": [PositionSpecs().IsBefore("noun"), ],
                "master-slave": [LinkSpecs().IsSlave("noun"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("noun"), ],
                "add-to-seq": True
            },
            {
                "id": "adj+",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "id": "comma",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "position": [PositionSpecs().IsBeforeIfExists("adv"), PositionSpecs().IsBefore('adj-seq')],
                        "add-to-seq": True
                    },
                    {
                        "id": "adv",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsAdverb(), ],
                        "position": [PositionSpecs().IsBefore("adj-seq"), ],
                        "master-slave": [LinkSpecs().IsSlave("adj-seq"), ],
                        "add-to-seq": False
                    },
                    {
                        "id": "adj-seq",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsAdjective(), ],
                        "position": [PositionSpecs().IsBefore("noun"), ],
                        "master-slave": [LinkSpecs().IsSlave("noun"), ],
                        "unwanted-links": [LinkSpecs().MastersExcept("noun"), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "id": "adj++",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "id": "and",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "position": [PositionSpecs().IsBeforeIfExists("adv"), PositionSpecs().IsBefore('adj-seq')],
                        "add-to-seq": True
                    },
                    {
                        "id": "adv++",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsAdverb(), ],
                        "position": [PositionSpecs().IsBefore("adj-seq"), ],
                        "master-slave": [LinkSpecs().IsSlave("adj-seq"), ],
                        "add-to-seq": False
                    },
                    {
                        "id": "adj-seq++",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsAdjective(), ],
                        "position": [PositionSpecs().IsBefore("noun"), ],
                        "master-slave": [LinkSpecs().IsSlave("noun"), ],
                        "unwanted-links": [LinkSpecs().MastersExcept("noun"), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "id": "noun",
                "required": RequiredSpecs().IsNecessary(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "add-to-seq": True
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
