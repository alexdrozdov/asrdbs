#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.specdefs.common import SequenceSpec
from parser.specdefs.defs import FsmSpecs, RequiredSpecs, LinkSpecs, RepeatableSpecs, PosSpecs, AnchorSpecs


class ParticipalGroupSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'participal-group')
        self.__compared_with = {}

        self.spec = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
            },
            {
                "id": "$PARENT::participal",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsParticipal(), ],
                "anchor": [AnchorSpecs().LocalSpecAnchor(), ]
            },
            {
                "id": "$PARENT::noun",
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                "incapsulate": ["noun-group", ],
                "incapsulate-on-overflow": ["basic-noun", ],
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ],
            },
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
            },
        ]
