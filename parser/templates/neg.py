import parser.spare


@parser.spare.at(name='neg', namespace='specs')
@parser.spare.constructable
def neg(body, *args, **kwargs):
    neg_info = body.pop('@neg')
    inner_body = body.pop('body')

    if isinstance(inner_body, list):
        inner_body = {
            "@id": "body",
            "@inherit": ["once"],
            "entries": inner_body
        }

    repeatable = "once" if neg_info['strict'] else "once-or-none"
    body["entries"] = [
        {
            "@id": "neg",
            "@inherit": [repeatable],
            "@word": ['не', ],
        },
        inner_body
    ]
    parser.spare.again()
