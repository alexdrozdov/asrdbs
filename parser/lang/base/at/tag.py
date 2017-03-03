import parser.spare
from parser.lang.base.rules.defs import AnchorSpecs


@parser.spare.at(name='tag', namespace='specs')
@parser.spare.constructable
def tag(body, *args, **kwargs):
    for tag_name in body.popaslist('@tag'):
        body.setkey('anchor', AnchorSpecs().Tag(tag_name))
