#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, RepeatableSpecs, LinkSpecs


class NounNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-noun')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "id": "$SPEC::noun",
                "repeatable": RepeatableSpecs().EqualOrMoreThan(2),
                "incapsulate": ["adj+-noun", ],
                "incapsulate-binding": "$THIS::$INCAPSULATED::noun",
                "master-slave": [LinkSpecs().IsSlave("$SPEC::noun[$INDEX(0)-1]"), ],
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
