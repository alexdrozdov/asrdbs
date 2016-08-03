#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.named import template


class CommaAndOrSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'comma-and-or')
        self.__compared_with = {}

        self.spec = template("@", "spec")(
            {
                "@id": "or",
                "@inherit": ["once", "anchor"],
                "uniq-items": [
                    {
                        "@id": "comma",
                        "@inherit": ["comma", "once"],
                        "merges-with": ["comma", ],
                    },
                    {
                        "@id": "and",
                        "@inherit": ["once", "union"],
                        "@word": [u'и', ],
                    },
                    {
                        "@id": "or",
                        "@inherit": ["once", "union"],
                        "@word": [u'или', ],
                    }
                ]
            }
        )
