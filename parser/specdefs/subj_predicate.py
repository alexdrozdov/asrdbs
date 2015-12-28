#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, PosSpecs
from parser.specdefs.validate import ValidatePresence
from parser.named import template


class SubjectPredicateSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'subj-predicate')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::subject-pre",
                "include": ["subject-group", ],
            },
            {
                "repeatable": RepeatableSpecs().EqualOrMoreThan(1),
                "id": "$PARENT::predicate",
                "pos_type": [PosSpecs().IsVerb(), ],
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::subject-post",
                "include": ["subject-group", ],
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::subject', '$SPEC::predicate'])
