#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class BasicAdjSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-adj')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "id": "$PARENT::adj",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsAdjective(), ],
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
