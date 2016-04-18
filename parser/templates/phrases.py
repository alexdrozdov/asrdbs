#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.templates.common
from parser.lang.defs import RepeatableSpecs, WordSpecs


class IncludeSpec(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(IncludeSpec, self).__init__('phrases')

    def __call__(self, phrases):
        r = []
        for i, p in enumerate(phrases):
            words = p.split()
            if len(words) == 1:
                r.append(
                    {
                        "id": "$PARENT::phr-{0}".format(i),
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [WordSpecs().IsWord([words[0], ]), ],
                    }
                )
                continue
            rr = []
            for j, w in enumerate(words):
                rr.append(
                    {
                        "id": "$PARENT::phr-{0}_w-{1}".format(i, j),
                        "repeatable": RepeatableSpecs().Once(),
                        "pos_type": [WordSpecs().IsWord([w, ]), ],
                    }
                )
            r.append(
                {
                    "id": "$PARENT::phr-{0}".format(i),
                    "repeatable": RepeatableSpecs().Once(),
                    "entries": rr
                }
            )
        return r
