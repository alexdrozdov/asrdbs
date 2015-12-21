#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, PosSpecs, AnchorSpecs
from parser.named import template


class BasicNounSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-noun')
        self.__compared_with = {}

        self.spec = template("spec")(
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            }
        )
