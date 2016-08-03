#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.named import template


class BasicAdvSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-adv')
        self.__compared_with = {}

        self.spec = template("@", "spec")(
            {
                "@id": "adj",
                "@inherit": ["basic-adv", "once", "anchor"],
            },
        )
