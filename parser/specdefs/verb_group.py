#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import LinkSpecs, RepeatableSpecs, AnchorSpecs
from parser.named import template


class VerbGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'verb-group')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::noun-group-pre",
                "incapsulate": ["noun-group", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "repeatable": RepeatableSpecs().Once(),
                "id": "$PARENT::predicate",
                "incapsulate": ["adv-verb", ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::noun-group-post",
                "incapsulate": ["noun-group", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            }
        ])
