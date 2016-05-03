#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, AnchorSpecs, WordSpecs, PosSpecs
from parser.named import template


class EntitySpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity')
        self.__compared_with = {}

        self.spec = template("spec")([
            # {
            #     "id": "$PARENT::definitive",
            #     # For adjectives and participals
            # },
            # {
            #     "id": "$PARENT::ownership",
            #     "repeatable": RepeatableSpecs().Any(),
            #     "dependency-of": template("dependency")("ownership"),
            #     "include": template("include")("entity-owner"),
            # },
            # {
            #     "id": "$PARENT::from",
            #     "dependency-of": template("dependency")("from"),
            #     "include": template("include")("entity-list-neg"),
            # },
            # {
            #     "id": "$PARENT::place",
            # },
            # {
            #     "id": "$PARENT::part",
            # },
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
                "id": "$PARENT::location",
                "repeatable": RepeatableSpecs().Any(),
                "dependency-of": template("dependency")(
                    "location"
                ),
                "include": template("include")("entity-location"),
            },
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
            {
                "id": "$PARENT::#pre#",
                "repeatable": RepeatableSpecs().Never(),
            },
            template("aggregate")(
                "$PARENT::aggregate",
                attributes={
                    "anchor": AnchorSpecs().LocalSpecAnchor(),
                },
                body=template("repeat")(
                    "$PARENT::entity-list",
                    {
                        "id": "$PARENT::entity-list",
                        "repeatable": RepeatableSpecs().Once(),
                        "entries": [
                            # {
                            #     "id": "$PARENT::#pre#",
                            #     "repeatable": RepeatableSpecs().Never(),
                            #     "dependency-of": "$PARENT::entity",
                            # },
                            {
                                "id": "$PARENT::entity",
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
            ]
        )
