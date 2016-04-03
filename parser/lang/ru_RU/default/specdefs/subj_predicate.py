#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, PosSpecs
from parser.lang.validate import ValidatePresence
from parser.named import template


class SubjectPredicateSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'subj-predicate')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::subject-pre",
                "include": {
                    "spec": "subject-group"
                },
            },
            {
                "repeatable": RepeatableSpecs().EqualOrMoreThan(1),
                "id": "$PARENT::predicate",
                "pos_type": [PosSpecs().IsVerb(), ],
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::subject-post",
                "include": {
                    "spec": "subject-group"
                },
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::subject', '$SPEC::predicate'])
