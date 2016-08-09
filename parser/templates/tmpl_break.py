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

    def __mk_continued_tag(self, tag):
        return u'#-continued' + unicode(tag)

    def __call__(self, body):
        break_tag = self.__mk_continued_tag(body.pop('@break'))
        body['tag'] = break_tag
