#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, RepeatableSpecs, PosSpecs, AnchorSpecs, CaseSpecs


class BasicSubjectSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-subject')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "repeatable": RepeatableSpecs().Once(),
                "id": "$PARENT:subject",
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq_items": [
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
                        "incapsulate": ["noun-group", ],
                    },
                ],
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "$SPEC::fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
