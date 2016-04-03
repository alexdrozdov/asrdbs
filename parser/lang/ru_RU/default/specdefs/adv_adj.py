#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec, LinkWeight
from parser.lang.defs import RepeatableSpecs, AnchorSpecs, LinkSpecs
from parser.lang.validate import ValidatePresence
from parser.named import template


class AdvAdjSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adv-adj')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("repeat")(
                "$PARENT::adv",
                repeatable=RepeatableSpecs().Once(),
                body={
                    "id": "$PARENT::adv",
                    "repeatable": RepeatableSpecs().Once(),
                    "include": {
                        "spec": "basic-adv"
                    },
                    "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
                },
                separator={'always': False}
            ),
            {
                "id": "$PARENT::adj",
                "repeatable": RepeatableSpecs().Once(),
                "include": {
                    "spec": "basic-adj"
                },
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::adv', '$SPEC::adj'])
