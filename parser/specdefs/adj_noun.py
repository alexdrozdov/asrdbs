#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class AdjNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adj+-noun')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
            },
            {
                "id": "$PARENT::adj-pre",
                "repeatable": RepeatableSpecs().Any(),
                "incapsulate": ["adv-adj", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "id": "$SPEC::noun",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "id": "$PARENT::adj-post",
                "repeatable": RepeatableSpecs().Any(),
                "incapsulate": ["adv-adj", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
            },
        ]

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::noun', '$SPEC::adj'])
