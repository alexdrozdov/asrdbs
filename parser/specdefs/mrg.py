#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, RepeatableSpecs, PosSpecs, AnchorSpecs


class MrgSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'mrg')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            },
            {
                "id": "$PARENT::s1",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsNoun(), ],
            },
            {
                "id": "$PARENT::s2",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "incapsulate": ["inc", ],
            },
            {
                "id": "$PARENT::s3",
                "repeatable": RepeatableSpecs().Once(),
                "incapsulate": ["comma-and-or", ],
            },
            {
                "id": "$PARENT::s4",
                "pos_type": [PosSpecs().IsNoun(), ],
                "repeatable": RepeatableSpecs().Once(),
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            },
        ]


class IncSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'inc')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            },
            {
                "id": "$PARENT::p1",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "id": "$PARENT::p2",
                "repeatable": RepeatableSpecs().Any(),
                "entries": [
                    {
                        "id": "$PARENT::n1",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["comma-and-or", ],
                    },
                    {
                        "id": "$PARENT::n2",
                        "pos_type": [PosSpecs().IsNoun(), ],
                        "repeatable": RepeatableSpecs().Once(),
                        "anchor": AnchorSpecs().LocalSpecAnchor(),
                    },
                    {
                        "id": "$PARENT::n3",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["comma-and-or", ],
                    },
                ]
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            },
        ]
