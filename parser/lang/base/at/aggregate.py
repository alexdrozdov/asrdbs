import uuid
import parser.spare
from parser.lang.base.rules.defs import AggregateSpecs


@parser.spare.at(name='aggregate', namespace='specs')
@parser.spare.constructable
def aggregate(body, *args, **kwargs):
    agg_info = body.pop('@aggregate')
    is_anchor = agg_info.get('is_anchor', False)

    if 'body' in body:
        inner_body = body.pop('body')
    elif 'uniq-items' in body:
        inner_body = {
            "@id": "body",
            "@inherit": ["once"],
            "uniq-items": body.pop('uniq-items')
        }
    elif 'entries' in body:
        inner_body = {
            "@id": "body",
            "@inherit": ["once"],
            "entries": body.pop('entries')
        }
    else:
        raise ValueError('neither body, nor entries nor uniq-entries')

    if isinstance(inner_body, dict):
        inner_body = [inner_body, ]

    agg_open_tag_name = 'agg-open-{0}'.format(uuid.uuid1())
    agg_close_tag_name = 'agg-close-{0}'.format(uuid.uuid1())

    agg_open = {
        "@id": "agg-open",
        "@inherit": ["once"],
        "closed-with": AggregateSpecs().CloseWith(
            "$TAG({0})".format(agg_close_tag_name)
        ),
        "virtual": True,
        "closed": False,
    }

    agg_close = {
        "@id": 'agg-close',
        "@inherit": ["once"],
        "@tag": agg_close_tag_name,
        "virtual": True,
        "closed": True,
        "add-to-seq": False,
    }

    if not is_anchor:
        agg_open['@tag'] = agg_open_tag_name
        agg_close['action'] = AggregateSpecs().Close("$TAG({0})".format(agg_open_tag_name))
    else:
        agg_open['@inherit'].append("anchor")
        agg_close['action'] = AggregateSpecs().Close("$LOCAL_SPEC_ANCHOR")

    body["entries"] = [agg_open, ] + inner_body + [agg_close, ]
    parser.spare.again()
