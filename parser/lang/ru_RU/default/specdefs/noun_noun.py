#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, LinkSpecs
from parser.named import template


class NounNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-noun')
        self.__compared_with = {}

        self.spec = template("spec")(
            {
                "id": "$SPEC::noun",
                "repeatable": RepeatableSpecs().EqualOrMoreThan(2),
                "include": {
                    "spec": "adj+-noun"
                },
                "master-slave": [LinkSpecs().IsSlave("$SPEC::noun[$INDEX(0)-1]"), ],
            }
        )
