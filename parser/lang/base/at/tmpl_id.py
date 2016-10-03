import parser.spare


@parser.spare.at(name='id', namespace='specs')
@parser.spare.constructable
def at_id(body, *args, **kwargs):
    id_v = body.pop('@id')
    body["id"] = "$PARENT::" + id_v
