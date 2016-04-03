#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, PosSpecs, AnchorSpecs
from parser.named import template


class BasicAdjSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'basic-adj')
        self.__compared_with = {}

        self.spec = template("spec")(
            {
                "id": "$PARENT::adj",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsAdjective(), ],
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
        )
