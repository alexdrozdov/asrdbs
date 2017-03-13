import parser.spare
from parser.spare.atjson import ErrorRerun


def split_inherit(inherit):
    inherit_body = []
    inherit_opener = []
    for i in inherit:
        if i in ['once', 'once-or-none', 'once-or-more', 'any', 'never']:
            inherit_body.append(i)
        else:
            inherit_opener.append(i)
    return inherit_body, inherit_opener


def move_body_keys(body, opener):
    inherit_body = []
    inherit_opener = []
    safe_keys = ['@id', 'id', 'repeatable', 'required', 'virtual', 'add-to-seq']
    while True:
        try:
            for k in body.keys():
                if k in safe_keys:
                    continue

                v = body.pop(k)
                if k == '@inherit':
                    inherit_body, inherit_opener = split_inherit(v)
                else:
                    opener[k] = v

                parser.spare.again()
        except ErrorRerun:
            continue
        break

    opener['@inherit'] = list(set(["once", ]) | set(inherit_opener))
    if inherit_body:
        body['@inherit'] = inherit_body


@parser.spare.at(name='with-siblings', namespace='specs')
@parser.spare.constructable
def with_siblings(body, *args, **kwargs):
    info = body.pop('@with-siblings')

    if 'entries' in body or 'uniq-items' in body:
        raise ValueError('@with-siblings is allowed for simple entries only')

    opener = {
        "@id": "opener",
        "sibling": {
            "role": "leader",
            "specs": info['specs']
        },
        "closed": False
    }

    move_body_keys(body, opener)

    body['entries'] = [
        opener,
        {
            "@id": "follower",
            "@inherit": ["any"],
            "sibling": {"role": "follower"},
            "closed": False
        },
        {
            "@id": "closer",
            "@inherit": ["once"],
            "sibling": {"role": "closer"},
            "add-to-seq": False,
            "virtual": True,
        }
    ]

    parser.spare.again()
