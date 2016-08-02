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
                    "@id": "modifiers",
                    "@repeats": ["any", "separator::strict"],
                    "body": {
                        "@id": "modifier",
                        "@inherit": ["once", ],
                        "entries": [
                            {
                                "@id": "adv",
                                "@inherit": ["basic-adv", "once"],
                                "@dependency-of": ["modifier"],
                            }
                        ]
                    },
                },
                {
                    "@id": "core",
                    "@inherit": ["basic-adj", "once", "anchor"],
                },
                {
                    "@id": "dependencies",
                    "@repeats": ["any", "separator::strict"],
                    "body": {
                        "@id": "dependency",
                        "@inherit": ["once", ],
                        "uniq-items": [
                            {
                                "@id": "entity",
                                "@inherit": ["once", ],
                                "@dependency-of": ["modifier"],
                                "@includes": {"name": "entity-list", "is_static": True},
                            }
                        ]
                    },
                },
            ]
        )
