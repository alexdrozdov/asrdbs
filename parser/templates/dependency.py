import parser.spare
from parser.lang.defs import DependencySpecs


@parser.spare.at(name='dependency-of', namespace='specs')
@parser.spare.constructable
def dependency_of(body, *args, **kwargs):
    master = None
    dp_info = body.pop('@dependency-of')
    dp_id = dp_info[0]
    if 2 <= len(dp_info):
        master = dp_info[1]
    if master is None:
        master = [DependencySpecs().DependencyOf("$LOCAL_SPEC_ANCHOR", dp_id), ]
    else:
        master = [DependencySpecs().DependencyOf(master, dp_id), ]
    body['dependency-of'] = master
