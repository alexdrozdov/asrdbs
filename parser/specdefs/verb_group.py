#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class VerbGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'verb-group')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::noun-group-pre",
                "incapsulate": ["noun-group", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "repeatable": RepeatableSpecs().Once(),
                "id": "$PARENT::predicate",
                "incapsulate": ["adv-verb", ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::noun-group-post",
                "incapsulate": ["noun-group", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            },
        ]
