import types
import functools
import common.config
from common.singleton import singleton


registry = {}


def register(instance, name, namespace):
    if namespace not in registry:
        registry[namespace] = {}
    registry[namespace][name] = instance
    return instance


class Autoreg(type):
    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        r = super().__prepare__(name, bases, **kwargs)
        userargs = kwargs['userargs']
        r['get_name'] = cls.get_name(userargs['name'])
        r['get_namespace'] = cls.get_name(userargs['namespace'])
        return r

    def __new__(cls, clsname, bases, namespace, **kwargs):
        return register(
            super().__new__(cls, clsname, bases, namespace),
            kwargs['userargs']['name'],
            kwargs['userargs']['namespace']
        )

    def __init__(cls, clsname, bases, namespace, **kwargs):
        return super().__init__(clsname, bases, namespace)

    def get_name(name):
        def get_name(*args, **kwargs):
            return name
        return get_name

    def get_namespace(namespace):
        def get_namespace(*args, **kwargs):
            return namespace
        return get_namespace


def make_autoreg(metaclass, **kwargs):
    def wrapper(cls):
        if isinstance(cls, types.FunctionType):
            return register(cls, kwargs['name'], kwargs['namespace'])
        else:
            kwargs_ = {'userargs': kwargs}
            namespace = cls.__dict__.copy()
            slots = namespace.get('__slots__', [])
            slots = slots if isinstance(slots, list) else [slots, ]
            slots += ['__dict__', '__weak_ref__']
            namespace = {k: v for k, v in namespace.items() if k not in slots}
            namespace.update(metaclass.__prepare__(cls.__name__, (), **kwargs_))
            return metaclass(cls.__name__, cls.__bases__, namespace, **kwargs_)
    return wrapper


def at(**kwargs):
    return make_autoreg(Autoreg, **kwargs)


def tokenmapper(**kwargs):
    return make_autoreg(
        constructable(Autoreg),
        namespace='tokenmapper',
        **kwargs
    )


def tokenizer(**kwargs):
    return make_autoreg(
        constructable(Autoreg),
        namespace='tokenizer',
        **kwargs
    )


def constructable(obj):
    def wrapper(*args, **kwargs):
        return obj
    return wrapper


class Named(object):
    def __init__(self, constructors, reusable=False, def_namespace=None):
        self.__reusable = reusable
        if self.__reusable:
            self.__objs = {
                obj.get_name(): obj for obj in [clsdef() for clsdef in constructors]
            }
        else:
            self.__objs = {
                (clsdef_obj[1].get_name(), clsdef_obj[1].get_namespace()):
                    clsdef_obj[0] for clsdef_obj in [(clsdef, clsdef()) for clsdef in constructors]
            }

    def __getitem__(self, name):
        if self.__reusable:
            return self.__objs[name]
        else:
            if name in self.__objs:
                return self.__objs[name]()
            if (name[0], None) in self.__objs:
                return self.__objs[(name[0], None)]()
            raise KeyError('Key {0}:{1} not found'.format(name[1], name[0]))


class _Templates(Named):
    def __init__(self):
        super(_Templates, self).__init__(self.__load_templates())

    def __load_templates(self):
        cfg = common.config.Config()
        return functools.reduce(
            lambda x, y: x + y,
            [self.__load_module(tmpl_dir).load_templates() for tmpl_dir in cfg['/parser/templates']],
            []
        )

    def __load_module(self, path):
        parts = [str(p) for p in path.split('/')]
        root = parts[0]
        parts = parts[1:]
        path = root
        obj = __import__(root, globals(), locals(), root)
        for p in parts:
            path += '.' + p
            obj = __import__(path, globals(), locals(), p)
        return obj


@singleton
class Templates(_Templates):
    pass


class SequentialFuncCall(object):
    def __init__(self, func_list):
        self.__func_list = func_list

    def __call__(self, *args, **kwargs):
        res = self.__func_list[0](*args, **kwargs)
        for f in self.__func_list[1:]:
            res = f(res)
        return res


def get(name, *args, **kwargs):
    namespace = kwargs.get('namespace', None)
    ns_dict = registry[namespace]
    if name in ns_dict:
        return ns_dict[name]()
    ns_dict = registry[None]
    if name in ns_dict:
        return ns_dict[name]()
    raise KeyError(
        'Named instance {0} not found in {1}'.format(
            name, namespace
        )
    )
