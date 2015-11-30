#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class ParticipalGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'participal-group')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
            },
            {
                "id": "$PARENT::participal",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsParticipal(), ],
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Any(),
                "pos_type": [PosSpecs().IsNoun(), ],
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
            },
        ]
