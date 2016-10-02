import parser.spare
from parser.lang.defs import AnchorSpecs


@parser.spare.at(name='tag', namespace='specs')
@parser.spare.constructable
def tag(body, *args, **kwargs):
    tag_name = body.pop('@tag')
    body["anchor"] = AnchorSpecs().Tag(tag_name)
