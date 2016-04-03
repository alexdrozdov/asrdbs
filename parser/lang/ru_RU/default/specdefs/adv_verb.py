#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec, LinkWeight
from parser.lang.defs import RepeatableSpecs, LinkSpecs, AnchorSpecs
from parser.lang.validate import ValidatePresence
from parser.named import template


class AdvVerbSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adv-verb')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("repeat")(
                "$PARENT::adv-pre",
                repeatable=RepeatableSpecs().Any(),
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
                "id": "$PARENT::verb",
                "repeatable": RepeatableSpecs().Once(),
                "include": {
                    "spec": "basic-verb"
                },
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            },
            template("repeat")(
                "$PARENT::adv-post",
                repeatable=RepeatableSpecs().Any(),
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
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::adv', '$SPEC::verb'])
