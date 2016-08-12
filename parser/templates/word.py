#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import WordSpecs


class TemplateId(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateId, self).__init__(
            'word',
            namespace=None,
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __extend_attr(self, body, attr, val):
        if attr in body:
            v = body[attr]
            if not isinstance(v, list):
                v = [v, ]
        else:
            v = []
        v.extend(val)
        body[attr] = v

    def __call__(self, body, *args):
        word_list = body.pop('@word')
        if not isinstance(word_list, (list, tuple)):
            word_list = [word_list, ]
        self.__extend_attr(
            body,
            "pos_type",
            [WordSpecs().IsWord(word_list), ]
        )