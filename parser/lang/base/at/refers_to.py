import parser.spare
from parser.lang.base.rules.defs import RefersToSpecs


@parser.spare.at(name='refers-to', namespace='specs')
@parser.spare.constructable
def refers_to(body, *args, **kwargs):
    refto_info = body.pop('@refers-to')
    master = refto_info.get('master', None)
    if master is None:
        master = "$LOCAL_SPEC_ANCHOR"
    body['refers-to'] = [RefersToSpecs().AttachTo(master), ]
