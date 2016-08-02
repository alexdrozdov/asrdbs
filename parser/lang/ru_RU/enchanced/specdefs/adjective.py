#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.named import template


class AdjectiveSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adjective')
        self.__compared_with = {}

        self.spec = template("@", "spec")(
            [
                {
                    "id": "$PARENT::modifiers",
                    "@repeats": ["any", "separator::strict"],
                    "body": {
                        "id": "$PARENT::modifier",
                        "@inherit": ["once", ],
                        "entries": [
                            {
                                "id": "$PARENT::adv",
                                "@inherit": ["basic-adv", "once"],
                                "@dependency-of": ["modifier"],
                            }
                        ]
                    },
                },
                {
                    "id": "$PARENT::core",
                    "@inherit": ["basic-adj", "once", "anchor"],
                },
                {
                    "id": "$PARENT::dependencies",
                    "@repeats": ["any", "separator::strict"],
                    "body": {
                        "id": "$PARENT::dependency",
                        "@inherit": ["once", ],
                        "uniq-items": [
                            {
                                "id": "$PARENT::entity",
                                "@inherit": ["once", ],
                                "@dependency-of": ["modifier"],
                                "@includes": {"name": "entity-list", "is_static": True},
                            }
                        ]
                    },
                },
            ]
        )
