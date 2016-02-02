#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import LinkSpecs, RepeatableSpecs, PosSpecs, AnchorSpecs
from parser.named import template


class ParticipalGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'participal-group')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::participal",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsParticipal(), ],
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "include": {
                    "spec": "noun-group"
                },
                "incapsulate-on-overflow": ["basic-noun", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            }
        ])
