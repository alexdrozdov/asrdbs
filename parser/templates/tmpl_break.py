#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common


class TemplateBreak(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateBreak, self).__init__(
            'break',
            namespace='selectors',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __mk_break_tag(self, tag):
        return '#break-' + str(tag)

    def __mk_fwd_tag(self, tag):
        return '#break-fwd-' + str(tag)

    def __mk_continued_tag(self, tag):
        return '#continued-' + str(tag)

    def __call__(self, body):
        tag = body.pop('@break')
        body['tag'] = self.__mk_break_tag(tag)
        body['clarify'] = {
            'tag': self.__mk_fwd_tag(tag),
            'clarifies': [self.__mk_continued_tag(tag)]
        }
