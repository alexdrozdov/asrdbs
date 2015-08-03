#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class AdjNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-noun')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "id": "$THIS::noun",
                "required": RequiredSpecs().IsNecessary(),
                "repeatable": RepeatableSpecs.EqualOrMoreThan(2),
                "incapsulate": ["adj-noun", ],
                "incapsulate-simlink": "$THIS::adj-noun::noun",
                "incapsulate-compile": True,
                "master-slave": [LinkSpecs().IsSlave(GroupSpecs().LastEntry("seq-nouns")), ],
                "group": ["seq-nouns", ]
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
