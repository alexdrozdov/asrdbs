#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common


class TemplateNeg(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'neg',
            namespace=None,
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        neg_info = body.pop('@neg')
        inner_body = body.pop('body')

        if isinstance(inner_body, list):
            inner_body = {
                "@id": "body",
                "@inherit": ["once"],
                "entries": inner_body
            }

        repeatable = "once" if neg_info['strict'] else "once-or-none"
        body["entries"] = [
            {
                "@id": "neg",
                "@inherit": [repeatable],
                "@word": ['не', ],
            },
            inner_body
        ]
        raise parser.templates.common.ErrorRerun()
