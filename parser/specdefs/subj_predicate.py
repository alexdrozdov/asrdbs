#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.speccmn import *


class SubjectPredicateSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self, 'subj-predicate')
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "subject",
                "pos_type": [PosSpecs().IsSuject(), ],
                "case": [CaseSpecs().IsCase(["nominative", ]), ],
                "position": [PositionSpecs().IsBefore("predicate"), ],
                "unwanted-links": [LinkSpecs().AllMasters(), ],
                "add-to-seq": True
            },
            {
                "id": "subj+",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "required": RequiredSpecs().IsOptional(),
                        "id": "spacer-1",
                        "pos_type": [PosSpecs().IsExcept(["noun", "pronoun", "verb"]), ],
                        "add-to-seq": False
                    },
                    {
                        "required": RequiredSpecs().IsNecessary(),
                        "id": "subject+",
                        "pos_type": [PosSpecs().IsSuject(), ],
                        "case": [CaseSpecs().IsCase(["nominative", ]), ],
                        "position": [PositionSpecs().IsBefore("predicate"), ],
                        "unwanted-links": [LinkSpecs().AllMasters(), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "id": "spacer-2",
                "pos_type": [PosSpecs().IsExcept(["noun", "pronoun", "verb"]), ],
                "add-to-seq": False
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "predicate",
                "pos_type": [PosSpecs().IsVerb(), ],
                "unwanted-links": [LinkSpecs().AllMasters(), ],
                "add-to-seq": True
            },
            {
                "id": "predic+",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "required": RequiredSpecs().IsOptional(),
                        "id": "spacer-3",
                        "pos_type": [PosSpecs().IsExcept(["noun", "pronoun", "verb"]), ],
                        "add-to-seq": False
                    },
                    {
                        "required": RequiredSpecs().IsNecessary(),
                        "id": "predicate+",
                        "pos_type": [PosSpecs().IsVerb(), ],
                        "unwanted-links": [LinkSpecs().AllMasters(), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]
