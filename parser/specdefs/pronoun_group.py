#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, PosSpecs, AnchorSpecs
from parser.specdefs.validate import ValidatePresence
from parser.named import template


class PronounGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'pronoun-group')
        self.__compared_with = {}

        self.spec = template("spec")([
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
                        "include": ["comma-and-or", ],
                    },
                    {
                        "id": "$PARENT::pronoun",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsPronoun(), ],
                        "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
                    },
                ]
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::pronoun', ])
