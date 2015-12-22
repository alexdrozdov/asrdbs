#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.specdefs.defs import RepeatableSpecs


class TemplateRepeat(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateRepeat, self).__init__('repeat')

    def __call__(self, entry_id, body, repeatable, separator=None):
        assert repeatable is not None
        if isinstance(body, list):
            body = \
                {
                    "id": entry_id,
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": body
                }
        if separator is None:
            separator = \
                {
                    "id": "$PARENT::comma-and-or",
                    "repeatable": RepeatableSpecs().Once(),
                    "incapsulate": ["comma-and-or", ],
                }
        elif isinstance(separator, dict):
            optional = separator.has_key('always') and not separator['always']
            separator = separator['separator'] if separator.has_key('separator') else None
            if separator is None:
                separator = \
                    {
                        "id": "$PARENT::comma-and-or",
                        "repeatable": RepeatableSpecs().Once(),
                        "incapsulate": ["comma-and-or", ],
                    }
                if optional:
                    separator['repeatable'] = RepeatableSpecs().LessOrEqualThan(1)

        return \
            {
                "id": entry_id,
                "repeatable": repeatable,
                "entries":
                [
                    {
                        "id": "$PARENT::optional",
                        "repeatable": RepeatableSpecs().Any(),
                        "entries":
                        [
                            body,
                            separator,
                        ]
                    },
                    body
                ]
            }
