#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, LinkSpecs
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
                "incapsulate-binding": "$THIS::$INCAPSULATED::noun",
                "master-slave": [LinkSpecs().IsSlave("$SPEC::noun[$INDEX(0)-1]"), ],
            }
        )
