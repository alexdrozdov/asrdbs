#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, AnchorSpecs, WordSpecs, PosSpecs
from parser.named import template


class EntityListSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-list')
        self.__compared_with = {}

        self.spec = template("@", "spec")([
            template("aggregate")(
                "$PARENT::aggregate",
                attributes={
                    "anchor": AnchorSpecs().LocalSpecAnchor(),
                },
                body={
                    "@id": "variants",
                    "@inherit": ["once"],
                    "uniq-items": [
                        {
                            "@id": "common-pre",
                            "@inherit": ["once"],
                            "entries": [
                                {
                                    "@id": "#pre#",
                                    "repeatable": RepeatableSpecs().Never(),
                                },
                                template("repeat")(
                                    "$PARENT::entity-list",
                                    {
                                        "id": "$PARENT::entity-list",
                                        "repeatable": RepeatableSpecs().Once(),
                                        "entries": [
                                            {
                                                "id": "$PARENT::#item#",
                                                "@inherit": ["once"],
                                                "refers-to": template("refers-to")(),
                                                "anchor": AnchorSpecs().Tag("object"),
                                                "include": template("include")("entity-neg", is_static=True),
                                            }
                                        ]
                                    },
                                    repeatable=RepeatableSpecs().Once(),
                                    separator=None
                                ),
                            ]
                        },
                        template("repeat")(
                            "$PARENT::entity-list",
                            {
                                "id": "$PARENT::entity-list",
                                "@inherit": ["once"],
                                "entries": [
                                    {
                                        "id": "$PARENT::#pre-internal#",
                                        "repeatable": RepeatableSpecs().Never(),
                                        "dependency-of": template("dependency")(
                                            "#obj-preposition",
                                            "$PARENT::#item#"
                                        ),
                                    },
                                    {
                                        "id": "$PARENT::#item#",
                                        "@inherit": ["once"],
                                        "refers-to": template("refers-to")(),
                                        "anchor": AnchorSpecs().Tag("object-int"),
                                        "include": template("include")("entity-neg", is_static=True),
                                    }
                                ]
                            },
                            repeatable=RepeatableSpecs().Once(),
                            separator=None
                        ),
                    ]
                },
                as_dict=True
            )
        ])


class EntityLocationSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-location')
        self.__compared_with = {}

        self.spec = template("subclass")(
            base=EntityListSpec,
            rewrite=[
                {
                    "find": {
                        "id": ".*::#pre#",
                    },
                    "extend": {
                        "id": "$PARENT::prepositions",
                        "anchor": AnchorSpecs().Tag("pre"),
                        "repeatable": RepeatableSpecs().Once(),
                        "uniq-items": template("foreach")(
                            prototype={
                                "repeatable": RepeatableSpecs().Once(),
                                "pos_type": [PosSpecs().IsPreposition(), ],
                                "dependency-of": template("dependency")(
                                    "#obj-preposition",
                                    "$TAG(object)"
                                ),
                            },
                            items=[
                                {"pos_type": [WordSpecs().IsWord(['над']), ]},
                                {"pos_type": [WordSpecs().IsWord(['под']), ]},
                                {"pos_type": [WordSpecs().IsWord(['в']), ]},
                                {"pos_type": [WordSpecs().IsWord(['на']), ]},
                            ]
                        )
                    }
                },
                {
                    "find": {
                        "id": ".*::#pre-internal#",
                    },
                    "extend": {
                        "id": "$PARENT::prepositions",
                        "repeatable": RepeatableSpecs().Once(),
                        "uniq-items": template("foreach")(
                            prototype={
                                "repeatable": RepeatableSpecs().Once(),
                                "pos_type": [PosSpecs().IsPreposition(), ],
                                "exclusive-with": AnchorSpecs().ExclusiveWith("$TAG(pre)"),
                            },
                            items=[
                                {"pos_type": [WordSpecs().IsWord(['над']), ]},
                                {"pos_type": [WordSpecs().IsWord(['под']), ]},
                                {"pos_type": [WordSpecs().IsWord(['в']), ]},
                                {"pos_type": [WordSpecs().IsWord(['на']), ]},
                            ]
                        )
                    }
                },
            ]
        )
