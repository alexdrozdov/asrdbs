#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, PosSpecs, AnchorSpecs, CaseSpecs
from parser.named import template


class BasicSubjectSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-subject')
        self.__compared_with = {}

        self.spec = template("spec")(
            {
                "repeatable": RepeatableSpecs().Once(),
                "id": "$PARENT:subject",
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq-items": [
                    {
                        "id": "$PARENT::pronoun",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsPronoun(), ],
                        "case": [CaseSpecs().IsCase(["nominative", ]), ],
                    },
                    {
                        "id": "$PARENT::noun",
                        "repeatable": RepeatableSpecs().Once(),
                        "case": [CaseSpecs().IsCase(["nominative", ]), ],
                        "include": {
                            "spec": "noun-group"
                        },
                    },
                ],
            }
        )
