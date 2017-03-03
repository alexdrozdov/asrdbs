import parser.spare
from parser.lang.base.rules.defs import RefersToSpecs


@parser.spare.at(name='refers-to', namespace='specs')
@parser.spare.constructable
def refers_to(body, *args, **kwargs):
    for refto_info in body.popaslist('@refers-to'):
        master = refto_info.get('master', "$LOCAL_SPEC_ANCHOR")
        selectors = refto_info.get('selectors')
        body.setkey(
            'refers-to',
            RefersToSpecs().AttachTo(master, selectors=selectors))
