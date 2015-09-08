#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class BasicSubjectSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-subject')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "case": [CaseSpecs().IsCase(["nominative", ]), ],
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
