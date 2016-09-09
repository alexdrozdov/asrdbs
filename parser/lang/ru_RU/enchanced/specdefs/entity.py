#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, AnchorSpecs, WordSpecs, PosSpecs
from parser.named import template


class EntitySpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity')
        self.__compared_with = {}

        self.spec = template("@", "spec")([
            {
                "@id": "definitive",
                "@inherit": ["any"],
                "@includes": {"name": "adjective"},
                "@dependency-of": ["location"]
            },
            {
                "@id": "core",
                "@inherit": ["once", "anchor"],
                "uniq-items": [
                    {
                        "@id": "noun",
                        "@inherit": ["#object", "once"],
                        "@includes": {"name": "basic-noun", "is_static": True},
                    }
                ]
            },
            {
                "@id": "ownership",
                "@inherit": ["any"],
                "uniq-items": [
                    {
                        "@id": "location",
                        "@inherit": ["once"],
                        "@includes": {"name": "entity-location"},
                        "@dependency-of": ["#entity-entity"]
                    }
                ]
            }
        ])


class EntityNegSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-neg')
        self.__compared_with = {}

        self.spec = template("@", "spec")([
            template("neg")(
                "$PARENT::entity-neg",
                {
                    "id": "$PARENT::body",
                    "@inherit": ["once", "anchor"],
                    "anchor": AnchorSpecs().LocalSpecAnchor(),
                    "include": template("include")("entity", is_static=True),
                },
                repeatable=RepeatableSpecs().Once(),
                strict_neg=False
            )
        ])


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
                    "id": "$PARENT::variants",
                    "@inherit": ["once"],
                    "uniq-items": [
                        {
                            "id": "$PARENT::common-pre",
                            "repeatable": RepeatableSpecs().Once(),
                            "entries": [
                                {
                                    "id": "$PARENT::#pre#",
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


class EntityListNegSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-list-neg')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("neg")(
                "$PARENT::entity-list-neg",
                "entity-list",
                repeatable=RepeatableSpecs().Once(),
                strict_neg=False,
                anchor=True
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
