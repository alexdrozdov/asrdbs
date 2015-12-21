#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import RepeatableSpecs, PosSpecs, AnchorSpecs
from parser.named import template


class BasicVerbSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-verb')
        self.__compared_with = {}

        self.spec = template("spec")(
            {
                "id": "$PARENT::verb",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsVerb(), ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            }
        )
