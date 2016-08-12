#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import parser.templates.common
from parser.lang.defs import AggregateSpecs, RepeatableSpecs, AnchorSpecs


class TemplateAggregate(parser.templates.common.SpecTemplate):
    def __init__(self):
        super(TemplateAggregate, self).__init__('aggregate')

    def __call__(self, entry_id, attributes, body, as_dict=False):
        if isinstance(body, dict):
            body = [body, ]

        agg_close_tag_name = 'agg-close-{0}'.format(uuid.uuid1())

        agg_open = {
            "id": entry_id,
            "virtual": True,
            "repeatable": RepeatableSpecs().Once(),
            "closed-with": AggregateSpecs().CloseWith(
                "$TAG({0})".format(agg_close_tag_name)
            ),
            "closed": False,
        }
        for k, v in list(attributes.items()):
            agg_open[k] = v

        agg_close = {
            "id": entry_id + '-close',
            "virtual": True,
            "repeatable": RepeatableSpecs().Once(),
            "anchor": AnchorSpecs().Tag(agg_close_tag_name),
            "action": AggregateSpecs().Close("$LOCAL_SPEC_ANCHOR"),
            "closed": True,
            "add-to-seq": False,
        }

        if 'anchor' not in agg_open:
            agg_open['anchor'] = AnchorSpecs().Tag("agg-open")
            agg_close['action'] = AggregateSpecs().Close("agg-open")
        elif agg_open['anchor'][1] == 1:  # local_spec_anchor
            agg_close['action'] = AggregateSpecs().Close("$LOCAL_SPEC_ANCHOR")
        else:  # tag with name
            assert agg_open['anchor'][2] is not None
            agg_close['action'] = AggregateSpecs().Close(agg_open['anchor'][2])

        res = [agg_open, ] + body + [agg_close, ]
        if not as_dict:
            return res
        return {
            "id": "$PARENT::agg",
            "repeatable": RepeatableSpecs().Once(),
            "entries": res
        }
