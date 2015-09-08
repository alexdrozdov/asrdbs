#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class SubjectGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'subject-group')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "id": "$PARENT::sub",
                "repeatable": RepeatableSpecs().EqualOrMoreThan(1),
                "entries": [
                    {
                        "id": "$PARENT::subject",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["basic-subject", ],
                    },
                    {
                        "id": "$PARENT::spacer",
                        "repeatable": RepeatableSpecs().Any(),
                        "pos_type": [PosSpecs().IsExcept(["noun", "pronoun", "verb"]), ],
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
