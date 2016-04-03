#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import LinkSpecs, RepeatableSpecs, AnchorSpecs
from parser.named import template


class VerbGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'verb-group')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::noun-group-pre",
                "include": {
                    "spec": "noun-group"
                },
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "repeatable": RepeatableSpecs().Once(),
                "id": "$PARENT::predicate",
                "include": {
                    "spec": "adv-verb"
                },
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            {
                "repeatable": RepeatableSpecs().Any(),
                "id": "$PARENT::noun-group-post",
                "include": {
                    "spec": "noun-group"
                },
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            }
        ])
