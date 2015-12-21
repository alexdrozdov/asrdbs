#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec, LinkWeight
from parser.specdefs.defs import RepeatableSpecs, LinkSpecs, AnchorSpecs
from parser.specdefs.validate import ValidatePresence
from parser.named import template


class AdvVerbSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adv-verb')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::adv-pre",
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
                "id": "$PARENT::verb",
                "repeatable": RepeatableSpecs().Once(),
                "incapsulate": ["basic-verb", ],
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            },
            {
                "id": "$PARENT::adv-post",
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
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::adv', '$SPEC::verb'])
