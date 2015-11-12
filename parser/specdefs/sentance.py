#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class SentanceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'sentance')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            },
            {
                "id": "$PARENT::subject-pre",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "incapsulate": ["subject-group", ],
            },
            {
                "id": "$PARENT::predicate",
                "repeatable": RepeatableSpecs().EqualOrMoreThan(1),
                "incapsulate": ["verb-group", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
            },
            {
                "id": "$PARENT::subject-post",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "incapsulate": ["subject-group", ],
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            },
        ]

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::subject', '$SPEC::predicate'])
