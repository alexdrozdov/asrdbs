import parser.spare


@parser.spare.at(name='includes', namespace='specs')
@parser.spare.constructable
def includes(body, *args, **kwargs):
    incl_info = body.pop('@includes')
    body['include'] = {
        "spec": incl_info['name'],
        "static-only": incl_info.get('is_static', False),
    }
