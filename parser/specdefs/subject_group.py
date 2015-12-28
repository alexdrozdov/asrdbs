#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, AnchorSpecs
from parser.named import template


class SubjectGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'subject-group')
        self.__compared_with = {}

        self.spec = template("spec")(
            {
                "id": "$PARENT::subject",
                "repeatable": RepeatableSpecs().Once(),
                "include": ["basic-subject", ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            }
        )
