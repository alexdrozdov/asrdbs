import parser.spare
from parser.lang.defs import WordSpecs


def extend_attr(body, attr, val):
    if attr in body:
        v = body[attr]
        if not isinstance(v, list):
            v = [v, ]
    else:
        v = []
    v.extend(val)
    body[attr] = v


@parser.spare.at(name='word', namespace=None)
@parser.spare.constructable
def word(body, *args, **kwargs):
    word_list = body.pop('@word')
    if not isinstance(word_list, (list, tuple)):
        word_list = [word_list, ]
    extend_attr(
        body,
        "pos_type",
        [WordSpecs().IsWord(word_list), ]
    )
