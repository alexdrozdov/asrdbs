#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, AnchorSpecs
from parser.named import template


class AdjectiveSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'adjective')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("repeat")(
                "$PARENT::modifiers",
                {
                    "id": "$PARENT::modifier",
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": [
                        {
                            "id": "$PARENT::adv",
                            "repeatable": RepeatableSpecs().Once(),
                            "include": template("include")("basic-adv", is_static=True),
                            "dependency-of": template("dependency")(
                                "modifier",
                                "$LOCAL_SPEC_ANCHOR"
                            ),
                        }
                    ]
                },
                repeatable=RepeatableSpecs().Any(),
                separator=None
            ),
            {
                "id": "$PARENT::core",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq-items": [
                    {
                        "id": "$PARENT::adj",
                        "repeatable": RepeatableSpecs().Once(),
                        "include": template("include")("basic-adj", is_static=True),
                    },
                ],
            },
            template("repeat")(
                "$PARENT::dependencies",
                {
                    "id": "$PARENT::dependency",
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": [
                        {
                            "id": "$PARENT::entity",
                            "repeatable": RepeatableSpecs().Once(),
                            "include": template("include")("entity-list", is_static=True),
                            "dependency-of": template("dependency")(
                                "modifier",
                                "$LOCAL_SPEC_ANCHOR"
                            ),
                        }
                    ]
                },
                repeatable=RepeatableSpecs().Any(),
                separator=None
            ),
        ])
