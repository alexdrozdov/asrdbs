import parser.spare
from parser.lang.base.rules.defs import SelectorSpecs


@parser.spare.at(name='selector', namespace='specs')
@parser.spare.constructable
def selector(body, *args, **kwargs):
    name = body.pop('@selector')
    body['selector'] = SelectorSpecs().Selector(name)
