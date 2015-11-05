#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class NounGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-group')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            },
            {
                "id": "$PARENT::preposition",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "pos_type": [PosSpecs().IsPreposition(), ],
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "incapsulate": ["adj+-noun", ],
                "master-slave": [LinkSpecs().IsSlave("$SPEC::preposition"), ],
            },
            {
                "id": "$PARENT::noun-seq",
                "repeatable": RepeatableSpecs().Any(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "incapsulate": ["noun-group-aux", ],
                "master-slave": [LinkSpecs().IsSlave("$SPEC::preposition"), ],
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            },
        ]

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::noun', ])


class NounGroupAuxSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-group-aux')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            },
            {
                "id": "$PARENT::comma-and-or",
                "repeatable": RepeatableSpecs().Once(),
                "incapsulate": ["comma-and-or", ],
                # "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "incapsulate": ["adj+-noun", ],
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            },
        ]
