import copy
import parser.spare


@parser.spare.at(name='foreach', namespace=None)
@parser.spare.constructable
def foreach(body, *args, **kwargs):
    prototype = body.pop('@foreach')
    if 'entries' in body:
        lst = body['entries']
    elif 'uniq-items' in body:
        lst = body['uniq-items']
    else:
        raise ValueError("neither entries nor uniq-items found")

    for i, item in enumerate(lst):
        p = copy.deepcopy(prototype)
        for k, v in list(p.items()):
            if k in item and isinstance(p[k], list):
                item[k].extend(v)
            else:
                item[k] = v
        item["@id"] = "phr-{0}".format(i)
    parser.spare.again()
