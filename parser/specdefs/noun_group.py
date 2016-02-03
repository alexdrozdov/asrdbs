#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, PosSpecs, AnchorSpecs, LinkSpecs, SameAsSpecs, CaseSpecs
from parser.specdefs.validate import ValidatePresence
from parser.named import template


class NounGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-group')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::preposition",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "pos_type": [PosSpecs().IsPreposition(), ],
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "include": {
                    "spec": "noun-ctrl-noun"
                },
                "master-slave": [LinkSpecs().IsSlave("$SPEC::preposition"), ],
            },
            {
                "id": "$PARENT::noun-seq",
                "repeatable": RepeatableSpecs().Any(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "same-as": [SameAsSpecs().SameCase("$PARENT::noun"), ],
                "include": {
                    "spec": "noun-group-aux"
                },
                "master-slave": [LinkSpecs().IsSlave("$SPEC::preposition"), ],
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::noun', ])


class NounGroupAuxSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-group-aux')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::comma-and-or",
                "repeatable": RepeatableSpecs().Once(),
                "include": {
                    "spec": "comma-and-or"
                },
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "include": {
                    "spec": "noun-ctrl-noun"
                },
            }
        ])


class NounCtrlNounSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'noun-ctrl-noun')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "include": {
                    "spec": "adj+-noun"
                },
            },
            {
                "id": "$PARENT::ctrled-noun",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "entries": [
                    {
                        "id": "$PARENT::noun",
                        "repeatable": RepeatableSpecs().Once(),
                        "master-slave": [LinkSpecs().IsSlave("$SPEC::noun"), ],
                        "case": [CaseSpecs().IsCase(["genitive", ]), ],
                        "include": {
                            "spec": "adj+-noun"
                        },
                    },
                    {
                        "id": "$PARENT::ctrled-noun",
                        "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                        "master-slave": [LinkSpecs().IsSlave("$SPEC::ctrled-noun::noun"), ],
                        "case": [CaseSpecs().IsCase(["genitive", ]), ],
                        "include": {
                            "spec": "adj+-noun"
                        },
                    }
                ]
            }
        ])
