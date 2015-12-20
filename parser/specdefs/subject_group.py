#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, RepeatableSpecs, AnchorSpecs


class SubjectGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'subject-group')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            },
            {
                "id": "$PARENT::subject",
                "repeatable": RepeatableSpecs().Once(),
                "incapsulate": ["basic-subject", ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            },
        ]
