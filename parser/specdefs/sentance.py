#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec, LinkWeight
from parser.specdefs.defs import RepeatableSpecs, LinkSpecs, AnchorSpecs
from parser.specdefs.validate import ValidatePresence
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
                "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
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
