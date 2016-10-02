import copy
import parser.spare.index


class ErrorRerun(Exception):
    pass


def again():
    raise ErrorRerun()


class AtJson(object):
    def __init__(self, namespace):
        self.__namespace = namespace

    def preprocess(self, spec, scope=None):
        spec = copy.deepcopy(spec)

        while True:
            try:
                for d, k, v in self.__iterspec(spec):
                    if k[0] == '@':
                        self.__handle_tmpl(d, k, scope)
                break
            except ErrorRerun:
                continue
            except:
                print(d, k, v)
                raise

        return spec

    def __handle_tmpl(self, d, k, scope):
        k = k.replace('@', '')
        tmpl = parser.spare.index.get(k, namespace=self.__namespace)
        tmpl(d, scope=scope)

    def __handle_val_tmpl(self, v):
        return v

    def __iterspec(self, rule, exclude=None):
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude, ]
        keys = list(filter(
            lambda k: k not in exclude,
            list(rule.keys()),
        ))

        for k in keys:
            v = rule[k]
            if isinstance(v, dict):
                for dd, kk, vv in self.__iterspec(v):
                    yield dd, kk, vv
            elif isinstance(v, list):
                for dd, kk, vv in self.__iterlist(v):
                    yield dd, kk, vv

            yield rule, k, v

    def __iterlist(self, l):
        for i in range(len(l)):
            v = l[i]
            if isinstance(v, str):
                if v[0] == '@':
                    l[i] = self.__handle_val_tmpl(v)
            elif isinstance(v, dict):
                for dd, kk, vv in self.__iterspec(v):
                    yield dd, kk, vv
            elif isinstance(v, list):
                for dd, kk, vv in self.__iterspec(v):
                    yield dd, kk, vv
