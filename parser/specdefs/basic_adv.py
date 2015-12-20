#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, RepeatableSpecs, PosSpecs, AnchorSpecs


class BasicAdvSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-adv')
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
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsAdverb(), ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
