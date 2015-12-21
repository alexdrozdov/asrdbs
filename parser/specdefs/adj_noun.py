#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec, LinkWeight
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
                "incapsulate": ["pronoun-group", ],
                "case": [CaseSpecs().IsCase(["genitive", ]), ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
            },
            {
                "id": "$PARENT::participal",
                "repeatable": RepeatableSpecs().Any(),
                "incapsulate": ["participal-group", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "reliability": 1,
            },
            {
                "id": "$PARENT::adj-pre",
                "repeatable": RepeatableSpecs().Any(),
                "incapsulate": ["adv-adj", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
                "reliability": 1,
            },
            {
                "id": "$PARENT::pronoun-seq",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "incapsulate": ["pronoun-group", ],
                "case": [CaseSpecs().IsCase(["genitive", ]), ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
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
                "incapsulate": ["adv-adj", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("$LOCAL_SPEC_ANCHOR", weight=LinkWeight("$SPECNAME")), ],
                "reliability": 0.9,
            },
            {
                "id": "$PARENT::participal-post",
                "repeatable": RepeatableSpecs().Any(),
                "reliability": 1,
                "entries": [
                    {
                        "id": "$PARENT::comma-open",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsComma(), ],
                    },
                    {
                        "id": "$PARENT::participal",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["participal-group", ],
                        "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
                    },
                    {
                        "id": "$PARENT::comma-close",
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [PosSpecs().IsComma(), ],
                    },
                ]
            }
        ])

    def get_validate(self):
        return ValidatePresence(self, ['$SPEC::noun', '$SPEC::adj'])
