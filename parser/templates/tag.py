#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import AnchorSpecs


class TemplateTag(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'tag',
            namespace='specs',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        tag_name = body.pop('@tag')
        body["anchor"] = AnchorSpecs().Tag(tag_name)
