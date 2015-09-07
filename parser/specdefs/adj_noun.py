#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class AdjNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adj+-noun')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT:adj-pre",
                "incapsulate": ["adv-adj", ]
            },
            {
                "id": "$SPEC::noun",
                "required": RequiredSpecs().IsNecessary(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "add-to-seq": True,
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT:adj-post",
                "incapsulate": ["adv-adj", ]
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
