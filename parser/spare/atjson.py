import copy
import parser.spare.index
from contextlib import contextmanager


class ErrorRerun(Exception):
    pass


def again():
    raise ErrorRerun()


@contextmanager
def until_complete():
    while True:
        try:
            yield
        except ErrorRerun:
            continue
        break


class DictWrap(object):

    expected_key_fmt = {
        'anchor': list,
        'case': list,
        'dependency-of': list,
        '@dependency-of': list,
        'neg': object,
        '@neg': object,
        'pos_type': list,
        'repeatable': object,
        'refers-to': list,
        'selector': list,
        '@selector': list,
    }

    def __init__(self, d):
        self.__d = d

    def setkey(self, k, val):
        expected_fmt = DictWrap.expected_key_fmt.get(k)
        if expected_fmt is None:
            raise ValueError('Unknown setkey fmt {0}'.format(k))

        if isinstance(val, list) and expected_fmt != list:
            raise ValueError('Setkey fmt {0} expects non-list value'.format(k))

        if expected_fmt == list:
            if not isinstance(val, list):
                val = [val, ]

            if k in self.__d:
                v = self.__d[k]
                if not isinstance(v, list):
                    v = [v, ]
            else:
                v = []

            v.extend(val)
            self.__d[k] = v
        else:
            self.__d[k] = val

    def popaslist(self, k):
        v = self.__d.pop(k)
        if isinstance(v, list):
            return v
        return [v, ]

    def __getattr__(self, name):
        return self.__d.__getattribute__(name)

    def __getitem__(self, k):
        return self.__d[k]

    def __setitem__(self, k, v):
        self.__d[k] = v

    def __contains__(self, k):
        return k in self.__d


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
        tmpl(DictWrap(d), scope=scope)

    def __handle_val_tmpl(self, v):
        return v

    def __sort_keys(self, keys, order):
        def cmpfcn(x, y):
            x_in_order = x in order
            y_in_order = y in order
            if not x_in_order and not y_in_order:
                return (x > y) - (y < x)
            if x_in_order and not y_in_order:
                return -1
            if y_in_order and not x_in_order:
                return 1
            x_index = order.index(x)
            y_index = order.index(y)
            return (x_index > y_index) - (x_index < y_index)

        return sorted(keys, key=cmp_to_key(cmpfcn))

    def __iterspec(self, rule, exclude=None):
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = [exclude, ]
        keys = list(filter(
            lambda k: k not in exclude,
            list(rule.keys()),
        ))

        for k in self.__sort_keys(keys, ['@subclass']):
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


def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K:
        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K
