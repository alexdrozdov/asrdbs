import uuid
import parser.spare
from parser.lang.sdefs import TermPropsSpecs


@parser.spare.at(name='bind-props', namespace='selectors')
@parser.spare.constructable
def bind_props(body, *args, **kwargs):
    bp = body.pop('@bind-props')
    body['bind-props'] = [TermPropsSpecs().Bind(int(bp)), ]
    body['tag'] = str(uuid.uuid1())
