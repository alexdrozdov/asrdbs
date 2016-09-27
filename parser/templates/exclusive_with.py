#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import AnchorSpecs


class ExclusiveWithId(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'exclusive-with',
            namespace='specs',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        exw_v = body.pop('@exclusive-with')[0]
        body["exclusive-with"] = AnchorSpecs().ExclusiveWith(exw_v)
