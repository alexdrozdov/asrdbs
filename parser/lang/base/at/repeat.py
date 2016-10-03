import copy
import parser.spare


@parser.spare.at(name='repeats', namespace='specs')
class TemplateAtRepeat(object):
    def __unroll_attrs(self, attrs):
        if isinstance(attrs, list):
            return self.__unroll_list_attrs(attrs)
        if isinstance(attrs, dict):
            return self.__unroll_dict_attrs(attrs)
        raise ValueError('Unsupported repeats attrs of type {0}'.format(
            type(attrs))
        )

    def __unroll_list_attrs(self, attrs):
        separator = None
        for a in attrs:
            if a == 'separator::strict':
                separator = {
                    "@id": "comma-and-or",
                    "@inherit": ["once"],
                    "@includes": {"name": "comma-and-or", "is_static": True}
                }
            elif a == 'separator::optional':
                separator = {
                    "@id": "comma-and-or",
                    "@inherit": ["once-or-none"],
                    "@includes": {"name": "comma-and-or", "is_static": True}
                }
            else:
                raise ValueError('Unsupported attrs {0}'.format(a))
        return separator

    def __unroll_dict_attrs(self, attrs):
        raise ValueError('Unsupported dict format')

    def __get_id_pair(self, body):
        if 'id' in body:
            return 'id', body['id']
        if '@id' in body:
            return '@id', body['@id']
        raise KeyError('Neither id nor @id found')

    def __call__(self, body, *args, **kwargs):
        attrs = body.pop('@repeats')

        assert 'body' in body or 'entries' in body
        assert not ('body' in body and 'entries' in body)
        if 'body' in body:
            inner_body = body.pop('body')
        elif 'entries' in body:
            inner_body = body.pop('entries')

        id_k, id_v = self.__get_id_pair(body)

        separator = self.__unroll_attrs(attrs)

        if isinstance(inner_body, list):
            inner_body = \
                {
                    id_k: id_v,
                    "@inherit": "once",
                    "entries": inner_body
                }

        body["entries"] = [
            {
                "@id": "optional",
                "@inherit": ["any"],
                "entries":
                [
                    inner_body,
                    separator,
                ]
            },
            copy.deepcopy(inner_body)
        ]
        parser.spare.again()
