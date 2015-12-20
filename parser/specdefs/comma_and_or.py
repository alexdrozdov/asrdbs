#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, RepeatableSpecs, PosSpecs, AnchorSpecs, WordSpecs


class CommaAndOrSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'comma-and-or')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "repeatable": RepeatableSpecs().Once(),
                "id": "$PARENT:or",
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq_items": [
                    {
                        "id": "$PARENT::comma",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "merges_with": ["comma", ],
                    },
                    {
                        "id": "$PARENT::and",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [WordSpecs().IsWord([u'и', ]), PosSpecs().IsUnion()],
                    },
                    {
                        "id": "$PARENT::or",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [WordSpecs().IsWord([u'или', ]), ],
                    }
                ]
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
