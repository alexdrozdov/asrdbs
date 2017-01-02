import re
import copy
import parser.spare


@parser.spare.at(name='subclass', namespace='specs')
class TemplateSubclass(object):
    def __call__(self, body, *args, **kwargs):
        superclass_spec_name = body.pop('@subclass')
        scope = kwargs['scope']
        spec = scope.spec(superclass_spec_name, original_json=True)
        spec = copy.deepcopy(spec)

        if 'rewrite' in body:
            rewrite = body.pop('rewrite')
            self.__rewrite_spec(spec, rewrite)

        self.__merge_spec(body, spec)
        parser.spare.again()

    def __rewrite_spec(self, spec, rewrite):
        for rule in rewrite:
            find = rule['find']
            extend = rule['extend']
            for e in self.__iterall(spec):
                if self.__rule_matched(e, find):
                    self.__rule_apply(e, extend)
                    break
            else:
                raise RuntimeError('Rule pattern not found {0} in {1}'.format(
                    find, spec
                ))

    def __merge_spec(self, body, spec):
        for k, v in spec.items():
            if k == 'name':
                continue
            body[k] = v

    def __iterall(self, l):
        if 'entries' in l:
            for ee in self.__iterall(l['entries']):
                yield ee
        if 'uniq-items' in l:
            for ee in self.__iterall(l['uniq-items']):
                yield ee
        if isinstance(l, dict):
            yield l
        if isinstance(l, list):
            for ee in l:
                for eee in self.__iterall(ee):
                    yield eee

    def __rule_matched(self, e, r):
        for k, v in list(r.items()):
            if k not in e and '@' + k not in e:
                return False
            if '@' + k in e:
                k = '@' + k
            if re.match(v, e[k]) is None:
                return False
        return True

    def __rule_apply(self, e, extend):
        for k, v in list(extend.items()):
            k_name = k.strip('@')
            if k_name in e:
                e.pop(k_name)
            k_name = '@' + k_name
            if k_name in e:
                e.pop(k_name)
            e[k] = v
