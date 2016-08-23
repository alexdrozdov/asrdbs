#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import parser.templates.common
from parser.lang.sdefs import TermPropsSpecs


class TemplateEnableProps(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateEnableProps, self).__init__(
            'enable-props',
            namespace='selectors',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __mk_enableprops_tag(self):
        return '#-enable-props' + str(uuid.uuid1())

    def __call__(self, body, *args):
        ep = body.pop('@enable-props')
        body['enable-props'] = [TermPropsSpecs().Enable(ep), ]
        if 'tag' not in body and '@tag' not in body:
            body['tag'] = self.__mk_enableprops_tag()
