#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


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
                "uniq_items": [
                    {
                        "id": "$PARENT::comma",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsComma(), ],
                    },
                    {
                        "id": "$PARENT::and",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [WordSpecs().IsWord([u'и', ]), ],
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
