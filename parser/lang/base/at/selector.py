import parser.spare
from parser.lang.base.rules.defs import SelectorSpecs


@parser.spare.at(name='selector', namespace='specs')
@parser.spare.constructable
def selector(body, *args, **kwargs):
    for name in body.popaslist('@selector'):
        body.setkey('selector', SelectorSpecs().Selector(name))
