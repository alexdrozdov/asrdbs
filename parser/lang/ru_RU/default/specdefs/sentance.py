#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, LinkSpecs, AnchorSpecs
from parser.lang.validate import ValidatePresence
from parser.named import template


class SentanceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'sentance')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::subject-pre",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "include": {
                    "spec": "subject-group"
                },
            },
            {
                "id": "$PARENT::predicate",
                "repeatable": RepeatableSpecs().EqualOrMoreThan(1),
                "include": {
                    "spec": "verb-group"
                },
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "id": "$PARENT::subject-post",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "include": {
                    "spec": "subject-group"
                },
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::subject', '$SPEC::predicate'])
