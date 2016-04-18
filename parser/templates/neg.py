#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import RepeatableSpecs, WordSpecs, AnchorSpecs


class TemplateNeg(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateNeg, self).__init__('neg')

    def __call__(self, entry_id, body, repeatable, strict_neg=False, anchor=False):
        assert repeatable is not None
        if isinstance(body, list):
            body = \
                {
                    "id": entry_id,
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": body
                }
        elif isinstance(body, str):
            body = \
                {
                    "id": "$PARENT::body",
                    "repeatable": RepeatableSpecs().Once(),
                    "include": {
                        "spec": body,
                        "static-only": True,
                    }
                }
        if anchor:
            body["anchor"] = AnchorSpecs().LocalSpecAnchor()
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
