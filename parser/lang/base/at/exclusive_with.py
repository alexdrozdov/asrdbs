import parser.spare
from parser.lang.base.rules.defs import AnchorSpecs


@parser.spare.at(name='exclusive-with', namespace='specs')
@parser.spare.constructable
def exclusive_with(self, body, *args, **kwargs):
    exw_v = body.pop('@exclusive-with')[0]
    body["exclusive-with"] = AnchorSpecs().ExclusiveWith(exw_v)
