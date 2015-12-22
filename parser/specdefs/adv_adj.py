#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec, LinkWeight
from parser.specdefs.defs import RepeatableSpecs, AnchorSpecs, LinkSpecs
from parser.specdefs.validate import ValidatePresence
from parser.named import template


class AdvAdjSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adv-adj')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("repeat")(
                "$PARENT::adv",
                repeatable=RepeatableSpecs().Any(),
                body={
                    "id": "$PARENT::adv",
                    "repeatable": RepeatableSpecs().Once(),
                    "incapsulate": ["basic-adv", ],
                    "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
                },
                separator={'always': False}
            ),
            {
                "id": "$PARENT::adj",
                "repeatable": RepeatableSpecs().Once(),
                "incapsulate": ["basic-adj", ],
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::adv', '$SPEC::adj'])
