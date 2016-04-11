#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import RepeatableSpecs, WordSpecs


class TemplateNeg(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateNeg, self).__init__('neg')

    def __call__(self, entry_id, body, repeatable=False, strict_neg=False):
        assert repeatable is not None
        if isinstance(body, list):
            body = \
                {
                    "id": entry_id,
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": body
                }
        return \
            {
                "id": entry_id,
                "repeatable": repeatable,
                "entries":
                [
                    {
                        "id": "$PARENT::neg",
                        "repeatable": RepeatableSpecs().Once() if strict_neg else RepeatableSpecs().LessOrEqualThan(1),
                        "pos_type": [WordSpecs().IsWord([u'не', ]), ],
                    },
                    body
                ]
            }
