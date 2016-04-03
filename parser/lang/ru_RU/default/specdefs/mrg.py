#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, PosSpecs, AnchorSpecs
from parser.named import template


class MrgSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'mrg')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::s1",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsNoun(), ],
            },
            {
                "id": "$PARENT::s2",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "include": {
                    "spec": "inc"
                },
            },
            {
                "id": "$PARENT::s3",
                "repeatable": RepeatableSpecs().Once(),
                "include": {
                    "spec": "comma-and-or"
                },
            },
            {
                "id": "$PARENT::s4",
                "pos_type": [PosSpecs().IsNoun(), ],
                "repeatable": RepeatableSpecs().Once(),
            }
        ])


class IncSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'inc')
        self.__compared_with = {}

        self.spec = template("spec")([
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
                        "include": {
                            "spec": "comma-and-or"
                        },
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
                        "include": {
                            "spec": "comma-and-or"
                        },
                    },
                ]
            }
        ])
