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
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$THIS::adj",
                "pos_type": [PosSpecs().IsAdjective(), ],
                "position": [PositionSpecs().IsBefore("$SPEC::noun"), ],
                "master-slave": [LinkSpecs().IsSlave("$SPEC::noun"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("$SPEC::noun"), ],
                "add-to-seq": True
            },
            {
                "id": "$THIS::adj+",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "id": "$THIS::comma",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "position": [PositionSpecs().IsBeforeIfExists("$THIS::adv"), PositionSpecs().IsBefore('$THIS::adj-seq')],
                        "add-to-seq": True
                    },
                    {
                        "id": "$THIS::adv",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsAdverb(), ],
                        "position": [PositionSpecs().IsBefore("$THIS::adj-seq"), ],
                        "master-slave": [LinkSpecs().IsSlave("$THIS::adj-seq"), ],
                        "add-to-seq": False
                    },
                    {
                        "id": "$THIS::adj-seq",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsAdjective(), ],
                        "position": [PositionSpecs().IsBefore("$SPEC::noun"), ],
                        "master-slave": [LinkSpecs().IsSlave("$SPEC::noun"), ],
                        "unwanted-links": [LinkSpecs().MastersExcept("$SPEC::noun"), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "id": "$THIS::adj++",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "id": "$THIS::and",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "position": [PositionSpecs().IsBeforeIfExists("$THIS::adv"), PositionSpecs().IsBefore('$THIS::adj-seq')],
                        "add-to-seq": True
                    },
                    {
                        "id": "$THIS::adv++",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsAdverb(), ],
                        "position": [PositionSpecs().IsBefore("$THIS::adj-seq"), ],
                        "master-slave": [LinkSpecs().IsSlave("$THIS::adj-seq"), ],
                        "add-to-seq": False
                    },
                    {
                        "id": "$THIS::adj-seq++",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsAdjective(), ],
                        "position": [PositionSpecs().IsBefore("$SPEC::noun"), ],
                        "master-slave": [LinkSpecs().IsSlave("$SPEC::noun"), ],
                        "unwanted-links": [LinkSpecs().MastersExcept("$SPEC::noun"), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "id": "$SPEC::noun",
                "required": RequiredSpecs().IsNecessary(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "add-to-seq": True
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
