import parser.spare


def mk_break_tag(tag):
    return '#break-' + str(tag)


def mk_fwd_tag(tag):
    return '#break-fwd-' + str(tag)


def mk_continued_tag(tag):
    return '#continued-' + str(tag)


@parser.spare.at(name='break', namespace='selectors')
@parser.spare.constructable
def at_break(body, *args, **kwargs):
    tag = body.pop('@break')
    body['tag'] = mk_break_tag(tag)
    body['clarify'] = {
        'tag': mk_fwd_tag(tag),
        'clarifies': [mk_continued_tag(tag)]
    }
