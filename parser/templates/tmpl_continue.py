#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common


class TemplateContinue(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateContinue, self).__init__(
            'continue',
            namespace='selectors',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __mk_continued_tag(self, tag):
        return '#-continued' + str(tag)

    def __call__(self, body, *args):
        tag = body.pop('@continue')
        continued_tag = self.__mk_continued_tag(tag)

        body_items = {}
        for k in list(body.keys()):
            body_items[k] = body.pop(k)

        if 'clarify' in body_items:
            body_items = body_items['clarify']

        body["multi"] = {
            "tag-base": continued_tag,
            "@self": {
                "clarify": body_items
            },
            "@other": {
            }
        }

        raise parser.templates.common.ErrorRerun()
