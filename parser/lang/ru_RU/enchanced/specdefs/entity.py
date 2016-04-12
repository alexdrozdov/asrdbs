#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.lang.common import SequenceSpec
from parser.lang.defs import RepeatableSpecs, AnchorSpecs
from parser.named import template


class EntitySpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity')
        self.__compared_with = {}

        self.spec = template("spec")([
            {
                "id": "$PARENT::definitive",
                # For adjectives and participals
            },
            {
                "id": "$PARENT::ownership",
                "dependency-off": template("dependency")("ownership"),
                "include": template("include")("entity-owner"),
            },
            {
                "id": "$PARENT::from",
                "dependency-off": template("dependency")("from"),
                "include": template("include")("entity-list-neg"),
            },
            {
                "id": "$PARENT::place",
            },
            {
                "id": "$PARENT::part",
            },
            {
                "id": "$PARENT::core",
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq-items": [
                    {
                        "id": "$PARENT::noun",
                        "repeatable": RepeatableSpecs().Once(),
                        "include": {
                            "spec": "basic-noun",
                        },
                    },
                    {
                        "id": "$PARENT::noun",
                        "repeatable": RepeatableSpecs().Once(),
                        "include": {
                            "spec": "basic-pronoun",
                        },
                    },
                ],
            }
        ])


class EntityNegSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-neg')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("neg")(
                "entity-neg",
                {
                    "id": "$PARENT::body",
                    "include": template("include")("entity"),
                },
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
            {
                "id": "$PARENT::aggregate",
                "repeatable": RepeatableSpecs().Virtual(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            template("repeat")(
                "$PARENT::entity-list",
                {
                    "id": "$PARENT::entity-list",
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": [
                        {
                            "id": "$PARENT::#pre#",
                            "repeatable": RepeatableSpecs().Never(),
                        },
                        {
                            "id": "$PARENT::entity",
                            "repeatable": RepeatableSpecs().Once(),
                            "refers-to": "$LOCAL_SPEC_ANCHOR",
                            "include": template("include")("entity-neg", is_static=True),
                        }
                    ]
                },
                repeatable=RepeatableSpecs().Once(),
                separator=None
            )
        ])


class EntityListNegSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-list-neg')
        self.__compared_with = {}

        self.spec = template("spec")([
            template("neg")(
                "entity-list-neg",
                {
                    "id": "$PARENT::body",
                    "include": template("include")("entity-list"),
                },
                strict_neg=False
            )
        ])


class EntityOwnerSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'entity-owner')
        self.__compared_with = {}

        self.spec = template("subclass")(
            base=EntityListNegSpec,
            rewrite=[
                {
                    "find": {
                        "id": "*::#pre#",
                    },
                    "extend": {
                        "dependency-off": "$PARENT::entity",
                        "repeatable": RepeatableSpecs().Once(),
                    }
                },
            ]
        )
