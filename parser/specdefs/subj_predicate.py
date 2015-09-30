#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class SubjectPredicateSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'subj-predicate')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::subject-pre",
                "incapsulate": ["subject-group", ],
            },
            {
                "repeatable": RepeatableSpecs().EqualOrMoreThan(1),
                "id": "$PARENT::predicate",
                "pos_type": [PosSpecs().IsVerb(), ],
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::subject-post",
                "incapsulate": ["subject-group", ],
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::subject', '$SPEC::predicate'])
