#!/usr/bin/env python
# -*- #coding: utf8 -*-


import copy
import parser.templates.common
from parser.lang.defs import RepeatableSpecs


class TemplateRepeat(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateRepeat, self).__init__('repeat')

    def __call__(self, entry_id, body, repeatable, separator=None):
        assert repeatable is not None
        if isinstance(body, list):
            body = \
                {
                    "id": entry_id,
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": body
                }
        if separator is None:
            separator = \
                {
                    "id": "$PARENT::comma-and-or",
                    "repeatable": RepeatableSpecs().Once(),
                    "include": {
                        "spec": "comma-and-or"
                    },
                }
        elif isinstance(separator, dict):
            optional = separator.has_key('always') and not separator['always']
            separator = separator['separator'] if separator.has_key('separator') else None
            if separator is None:
                separator = \
                    {
                        "id": "$PARENT::comma-and-or",
                        "repeatable": RepeatableSpecs().Once(),
                        "include": {
                            "spec": "comma-and-or"
                        },
                    }
                if optional:
                    separator['repeatable'] = RepeatableSpecs().LessOrEqualThan(1)

        return \
            {
                "id": entry_id,
                "repeatable": repeatable,
                "entries":
                [
                    {
                        "id": "$PARENT::optional",
                        "repeatable": RepeatableSpecs().Any(),
                        "entries":
                        [
                            body,
                            separator,
                        ]
                    },
                    body
                ]
            }


class TemplateAtRepeat(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateAtRepeat, self).__init__(
            'repeats',
            namespace=None,
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __unroll_attrs(self, attrs):
        if isinstance(attrs, list):
            return self.__unroll_list_attrs(attrs)
        if isinstance(attrs, dict):
            return self.__unroll_dict_attrs(attrs)
        raise ValueError('Unsupported repeats attrs of type {0}'.format(
            type(attrs))
        )

    def __unroll_list_attrs(self, attrs):
        repeatable = None
        separator = None
        for a in attrs:
            if a == 'any':
                repeatable = RepeatableSpecs().Any()
            elif a == 'once':
                repeatable = RepeatableSpecs().Once()
            elif a == 'separator::strict':
                separator = {
                    "id": "$PARENT::comma-and-or",
                    "repeatable": RepeatableSpecs().Once(),
                    "include": {
                        "spec": "comma-and-or"
                    },
                }
            elif a == 'separator::optional':
                separator = {
                    "id": "$PARENT::comma-and-or",
                    "repeatable": RepeatableSpecs().LessOrEqualThan(1),
                    "include": {
                        "spec": "comma-and-or"
                    },
                }
            else:
                raise ValueError('Unsupported attrs {0}'.format(a))
        return repeatable, separator

    def __unroll_dict_attrs(self, attrs):
        raise ValueError('Unsupported dict format')

    def __get_id_pair(self, body):
        if 'id' in body:
            return 'id', body['id']
        if '@id' in body:
            return '@id', body['@id']
        raise KeyError('Neither id nor @id found')

    def __call__(self, body, *args):
        attrs = body.pop('@repeats')
        inner_body = body.pop('body')
        id_k, id_v = self.__get_id_pair(body)

        repeatable, separator = self.__unroll_attrs(attrs)
        assert repeatable is not None

        if isinstance(inner_body, list):
            inner_body = \
                {
                    id_k: id_v,
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": body
                }

        body["repeatable"] = repeatable
        body["entries"] = [
            {
                "id": "$PARENT::optional",
                "repeatable": RepeatableSpecs().Any(),
                "entries":
                [
                    inner_body,
                    separator,
                ]
            },
            copy.deepcopy(inner_body)
        ]
