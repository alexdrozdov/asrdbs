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
            # {
            #     "id": "$PARENT::definitive",
            #     # For adjectives and participals
            # },
            # {
            #     "id": "$PARENT::ownership",
            #     "repeatable": RepeatableSpecs().Any(),
            #     "dependency-off": template("dependency")("ownership"),
            #     "include": template("include")("entity-owner"),
            # },
            # {
            #     "id": "$PARENT::from",
            #     "dependency-off": template("dependency")("from"),
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
                "dependency-off": template("dependency")("location"),
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
            {
                "id": "$PARENT::aggregate",
                "virtual": True,
                "repeatable": RepeatableSpecs().Once(),
                "anchor": AnchorSpecs().LocalSpecAnchor(),
                "uniq": None,
                "form-info": {
                    "part_of_speech": None,
                    "count": None,
                    "case": None,
                    "gender": None,
                },
            },
            template("repeat")(
                "$PARENT::entity-list",
                {
                    "id": "$PARENT::entity-list",
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": [
                        # {
                        #     "id": "$PARENT::#pre#",
                        #     "repeatable": RepeatableSpecs().Never(),
                        #     "dependency-off": "$PARENT::entity",
                        # },
                        {
                            "id": "$PARENT::entity",
                            "repeatable": RepeatableSpecs().Once(),
                            "refers-to": template("refers-to")(),
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
                        "dependency-off": "$PARENT::entity",
                        "repeatable": RepeatableSpecs().Once(),
                        "uniq-items": template("phrases")(
                            [u"на",
                             u"под",
                             u"в"]
                        )
                    }
                },
            ]
        )
