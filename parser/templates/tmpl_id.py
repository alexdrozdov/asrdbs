#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common


class TemplateId(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateId, self).__init__(
            'id',
            namespace=None,
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args):
        id_v = body.pop('@id')
        body["id"] = "$PARENT::" + id_v
