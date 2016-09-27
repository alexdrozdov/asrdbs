#!/usr/bin/env python
# -*- #coding: utf8 -*-


import copy
import parser.templates.common
from parser.lang.defs import PosSpecs, RepeatableSpecs, AnchorSpecs, LinkSpecs, CaseSpecs


class TemplateInherit(parser.templates.common.SpecTemplate):
    def __init__(self):
        super().__init__(
            'inherit',
            namespace='specs',
            args_mode=parser.templates.common.SpecTemplate.ARGS_MODE_NATIVE
        )

    def __call__(self, body, *args, **kwargs):
        inh_list = body.pop('@inherit')
        if not isinstance(inh_list, list):
            inh_list = [inh_list, ]
        rerun_required = False
        for base in inh_list:
            bb = self.__get_base(base)
            for k, v in list(bb.items()):
                rerun_required |= self.__extend_attr(body, k, v)
        if rerun_required:
            raise parser.templates.common.ErrorRerun()

    def __extend_attr(self, body, attr, val):
        if not isinstance(val, list):
            body[attr] = val
            return attr.startswith('@')

        if attr in body:
            v = body[attr]
            if not isinstance(v, list):
                v = [v, ]
        else:
            v = []
        v.extend(val)
        body[attr] = v
        return attr.startswith('@')

    def __get_base(self, base):
        bases = {
            'basic-adj': {
                "pos_type": [PosSpecs().IsAdjective(), ]
            },
            'basic-adv': {
                "pos_type": [PosSpecs().IsAdverb(), ]
            },
            'basic-noun': {
                "pos_type": [PosSpecs().IsNoun(), ]
            },
            'preposition': {
                "pos_type": [PosSpecs().IsPreposition(), ]
            },
            'union': {
                "pos_type": [PosSpecs().IsUnion(), ]
            },
            'comma': {
                "pos_type": [PosSpecs().IsComma(), ]
            },
            'once': {
                "repeatable": RepeatableSpecs().Once(),
            },
            'any': {
                "repeatable": RepeatableSpecs().Any(),
            },
            'once-or-none': {
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
            },
            'never': {
                "repeatable": RepeatableSpecs().Never(),
            },
            'anchor': {
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            'dependency': {
                "master-slave": [LinkSpecs().IsSlave("$LOCAL_SPEC_ANCHOR"), ]
            },
            '#object': {
                "@selector": "#object",
            },
            'genitive': {
                "case": [CaseSpecs().IsCase(["genitive", ]), ],
            },
            'soft-neg': {
                "@neg": {"strict": False},
            },
            'neg': {
                "@neg": {"strict": True},
            },
        }

        return copy.deepcopy(bases[base])
