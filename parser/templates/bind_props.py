#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import parser.templates.common
from parser.lang.sdefs import TermPropsSpecs


class TemplateBindProps(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateBindProps, self).__init__(
            'bind-props',
            namespace='selectors',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args):
        bp = body.pop('@bind-props')
        body['bind-props'] = [TermPropsSpecs().Bind(int(bp)), ]
        body['tag'] = str(uuid.uuid1())
