#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, RepeatableSpecs, PosSpecs, AnchorSpecs
from parser.specdefs.validate import ValidatePresence


class PronounGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'pronoun-group')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
            },
            {
                "id": "$PARENT::pronoun",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsPronoun(), ],
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            },
            {
                "id": "$PARENT::pronoun-seq",
                "repeatable": RepeatableSpecs().Any(),
                "entries":
                [
                    {
                        "id": "$PARENT::comma-and-or",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["comma-and-or", ],
                    },
                    {
                        "id": "$PARENT::pronoun",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsPronoun(), ],
                        "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
                    },
                ]
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
            },
        ]

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::pronoun', ])
