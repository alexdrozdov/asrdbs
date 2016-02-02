#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, PosSpecs, AnchorSpecs, CaseSpecs, LinkSpecs
from parser.specdefs.validate import ValidatePresence
from parser.named import template


class AdjNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adj+-noun')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::pronoun",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "include": {
                    "spec": "pronoun-group",
                },
                "case": [CaseSpecs().IsCase(["genitive", ]), ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "id": "$PARENT::participal",
                "repeatable": RepeatableSpecs().Any(),
                "include": {
                    "spec": "participal-group"
                },
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "reliability": 1,
            },
            {
                "id": "$PARENT::adj-pre",
                "repeatable": RepeatableSpecs().Any(),
                "include": {
                    "spec": "adv-adj"
                },
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "reliability": 1,
            },
            {
                "id": "$PARENT::pronoun-seq",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "include": {
                    "spec": "pronoun-group"
                },
                "case": [CaseSpecs().IsCase(["genitive", ]), ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "id": "$SPEC::noun",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "id": "$PARENT::adj-post",
                "repeatable": RepeatableSpecs().Any(),
                "include": {
                    "spec": "adv-adj"
                },
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "reliability": 0.9,
            },
            template("wrap")(
                "$PARENT::participal-post",
                repeatable=RepeatableSpecs().Any(),
                body={
                    "id": "$PARENT::participal",
                    "repeatable": RepeatableSpecs().Once(),
                    "include": {
                        "spec": "participal-group"
                    },
                    "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                },
                attrs={
                    "reliability": 1.0,
                }
            ),
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::noun', '$SPEC::adj'])
