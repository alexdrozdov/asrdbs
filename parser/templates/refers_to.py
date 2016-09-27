#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import RefersToSpecs


class DependencySpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(DependencySpec, self).__init__('refers-to')
        super().__init__(
            'refers-to',
            namespace='specs',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        refto_info = body.pop('@refers-to')
        master = refto_info.get('master', None)
        if master is None:
            master = "$LOCAL_SPEC_ANCHOR"
        body['refers-to'] = [RefersToSpecs().AttachTo(master), ]
