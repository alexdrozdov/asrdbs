import parser.spare


def mk_continued_tag(tag):
    return '#continued-' + str(tag)


@parser.spare.at(name='continue', namespace='selectors')
@parser.spare.constructable
def at_continue(body, *args, **kwargs):
    tag = body.pop('@continue')
    continued_tag = mk_continued_tag(tag)

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
    parser.spare.again()
