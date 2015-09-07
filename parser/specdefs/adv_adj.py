#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class AdvAdjSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adv-adj')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "id": "$PARENT::adv",
                "repeatable": RepeatableSpecs().Any(),
                "entries":
                [
                    {
                        "id": "$PARENT::adv",
                        "repeatable": RepeatableSpecs().Any(),
                        "entries":
                        [
                            {
                                "id": "$PARENT::adv",
                                "repeatable": RepeatableSpecs().Once(),
                                "incapsulate": ["basic-adv", ],
                                "incapsulate-binding": "$THIS::$INCAPSULATED::adv",
                                # "master-slave": [LinkSpecs().IsSlave("$SPEC::adj"), ],
                            },
                            {
                                "id": "$PARENT::comma-and-or",
                                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                                "incapsulate": ["comma-and-or", ],
                                "incapsulate-binding": "$THIS::$INCAPSULATED::adv",
                            }
                        ]
                    },
                    {
                        "id": "$PARENT::adv",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["basic-adv", ],
                        "incapsulate-binding": "$THIS::$INCAPSULATED::adv",
                        # "master-slave": [LinkSpecs().IsSlave("$SPEC::adj"), ],
                    },
                ]
            },
            {
                "id": "$PARENT::adj",
                "repeatable": RepeatableSpecs().Once(),
                "incapsulate": ["basic-adj", ],
                "incapsulate-binding": "$THIS::$INCAPSULATED::adj",
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
