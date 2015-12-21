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
            {
                "id": "$PARENT::adv",
                "repeatable": RepeatableSpecs().Any(),
                "entries":
                [
                    {
                        "id": "$PARENT::adv",
                        "repeatable": RepeatableSpecs().Any(),
                        "entries":
                        [
                            {
                                "id": "$PARENT::adv",
                                "repeatable": RepeatableSpecs().Once(),
                                "incapsulate": ["basic-adv", ],
                                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
                                "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
                            },
                            {
                                "id": "$PARENT::comma-and-or",
                                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                                "incapsulate": ["comma-and-or", ],
                            }
                        ]
                    },
                    {
                        "id": "$PARENT::adv",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["basic-adv", ],
                        "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                        "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
                    },
                ]
            },
            {
                "id": "$PARENT::adj",
                "repeatable": RepeatableSpecs().Once(),
                "incapsulate": ["basic-adj", ],
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::adv', '$SPEC::adj'])
