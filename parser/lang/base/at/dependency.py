import parser.spare
from parser.lang.base.rules.defs import DependencySpecs


@parser.spare.at(name='dependency-of', namespace='specs')
@parser.spare.constructable
def dependency_of(body, *args, **kwargs):
    for dependency in body.popaslist('@dependency-of'):
        if isinstance(dependency, str):
            selector = dependency
            master = "$LOCAL_SPEC_ANCHOR"
        else:
            selector = dependency['selector']
            master = dependency.get('master', "$LOCAL_SPEC_ANCHOR")
        body.setkey(
            'dependency-of',
            DependencySpecs().DependencyOf(master, selector))
