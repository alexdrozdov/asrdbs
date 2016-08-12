#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, PosSpecs, AnchorSpecs, WordSpecs
from parser.named import template


class CommaAndOrSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'comma-and-or')
        self.__compared_with = {}

        self.spec = template("spec")(
            {
                "repeatable": RepeatableSpecs().Once(),
                "id": "$PARENT:or",
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq-items": [
                    {
                        "id": "$PARENT::comma",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "merges-with": ["comma", ],
                    },
                    {
                        "id": "$PARENT::and",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [WordSpecs().IsWord(['и', ]), PosSpecs().IsUnion()],
                    },
                    {
                        "id": "$PARENT::or",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [WordSpecs().IsWord(['или', ]), ],
                    }
                ]
            }
        )
