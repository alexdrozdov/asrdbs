#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, AnchorSpecs, WordSpecs, PosSpecs, CaseSpecs
from parser.named import template


class EntitySpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::definitive",
                "repeatable": RepeatableSpecs().Any(),
                "dependency-of": template("dependency")(
                    "location"
                ),
                "include": template("include")("adjective"),
            },
            {
                "id": "$PARENT::core",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq-items": [
                    {
                        "id": "$PARENT::noun",
                        "repeatable": RepeatableSpecs().Once(),
                        "include": template("include")("basic-noun", is_static=True),
                    },
                    # {
                    #     "id": "$PARENT::noun",
                    #     "repeatable": RepeatableSpecs().Once(),
                    #     "include": {
                    #         "spec": "basic-pronoun",
                    #     },
                    # },
                ],
            },
            {
                "id": "$PARENT::ownership",
                "repeatable": RepeatableSpecs().Any(),
                "uniq-items": [
                    {
                        "id": "$PARENT::location",
                        "repeatable": RepeatableSpecs().Once(),
                        "dependency-of": template("dependency")(
                            "location"
                        ),
                        "include": template("include")("entity-location"),
                    },
                    {
                        "id": "$PARENT::ownership",
                        "repeatable": RepeatableSpecs().Once(),
                        "dependency-of": template("dependency")(
                            "location"
                        ),
                        "include": template("include")("entity-ownership"),
                    },
                ]
            }
        ])


class EntityNegSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-neg')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("neg")(
                "$PARENT::entity-neg",
                {
                    "id": "$PARENT::body",
                    "repeatable": RepeatableSpecs().Once(),
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

        self.spec = template("spec")([
            template("aggregate")(
                "$PARENT::aggregate",
                attributes={
                    "anchor": AnchorSpecs().LocalSpecAnchor(),
                },
                body={
                    "id": "$PARENT::variants",
                    "repeatable": RepeatableSpecs().Once(),
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
                                                "repeatable": RepeatableSpecs().Once(),
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
                                "repeatable": RepeatableSpecs().Once(),
                                "entries": [
                                    {
                                        "id": "$PARENT::#pre-internal#",
                                        "repeatable": RepeatableSpecs().Never(),
                                        "dependency-of": template("dependency")(
                                            "location",
                                            "$PARENT::#item#"
                                        ),
                                    },
                                    {
                                        "id": "$PARENT::#item#",
                                        "repeatable": RepeatableSpecs().Once(),
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
                                    "location",
                                    "$TAG(object)"
                                ),
                            },
                            items=[
                                {"pos_type": [WordSpecs().IsWord([u'над']), ]},
                                {"pos_type": [WordSpecs().IsWord([u'под']), ]},
                                {"pos_type": [WordSpecs().IsWord([u'в']), ]},
                                {"pos_type": [WordSpecs().IsWord([u'на']), ]},
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
                                {"pos_type": [WordSpecs().IsWord([u'над']), ]},
                                {"pos_type": [WordSpecs().IsWord([u'под']), ]},
                                {"pos_type": [WordSpecs().IsWord([u'в']), ]},
                                {"pos_type": [WordSpecs().IsWord([u'на']), ]},
                            ]
                        )
                    }
                },
            ]
        )


class EntityOwnershipSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-ownership')
        self.__compared_with = {}

        self.spec = template("subclass")(
            base=EntityListSpec,
            rewrite=[
                {
                    "find": {
                        "id": ".*::common-pre",
                    },
                    "extend": {
                        "repeatable": RepeatableSpecs().Never(),
                    }
                },
                {
                    "find": {
                        "id": ".*::#item#",
                    },
                    "extend": {
                        "case": [CaseSpecs().IsCase(["genitive", ]), ],
                    }
                },
            ]
        )
