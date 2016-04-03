#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import RepeatableSpecs, PosSpecs


class TemplateWrap(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateWrap, self).__init__('wrap')

    def __call__(self, entry_id, body, repeatable, before=None, after=None, attrs=None):
        if before is None:
            before = [{
                "id": "$PARENT::comma-open",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsComma(), ],
                "merges-with": ["comma", ],
            }, ]
        if after is None:
            after = [{
                "id": "$PARENT::comma-close",
                "repeatable": RepeatableSpecs().Once(),
                "pos_type": [PosSpecs().IsComma(), ],
                "merges-with": ["comma", ],
            }, ]
        if isinstance(body, dict):
            body = [body, ]

        res = \
            {
                "id": entry_id,
                "repeatable": repeatable,
                "entries": before + body + after
            }
        if attrs is not None:
            res.update(attrs)
        return res
