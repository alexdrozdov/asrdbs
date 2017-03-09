#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import copy
import common.config
import common.multijson
import parser.spare.rules
import parser.spare.atjson
from common.singleton import singleton
from parser.lang.base.rules.defs import RequiredSpecs, FsmSpecs


class PreprocessScope(object):
    def __init__(self):
        self.__specs = {}

    def add_specs(self, compiled_specs, source):
        for s in compiled_specs:
            self.__specs[s.get_name()] = {'spec': s, 'source': source}

    def spec(self, name, original_json=True):
        return self.__specs[name]['source']


class _Preprocessor(parser.spare.atjson.AtJson):
    def __init__(self):
        super().__init__(namespace='specs')


class _PreCompiler(object):
    def __init__(self):
        pass

    def compile(self, js, scope):
        js = Preprocessor().preprocess(js, scope)

        entries = [
            {
                "id": "$SPEC::init",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False,
            }
        ] + js['entries'] + [
            {
                "id": "$SPEC::fini",
                "required": RequiredSpecs().IsNecessary(),
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False,
            }
        ]
        return [parser.spare.rules.SequenceSpec(
            name=js['name'],
            spec=entries
        ), ]


class SpecDecl(object):
    def __init__(self, name):
        self.__name = name

    def name(self):
        return self.__name

    def declared(self):
        raise RuntimeError('not implemented')

    def format(self, fmt):
        raise RuntimeError('not implemented')


class SingleImplSpecDecl(SpecDecl):
    def __init__(self, impl, filename):
        super().__init__(impl['name'])
        self.__impl = impl
        self.__filename = filename

    def get_origin(self):
        return self.__filename

    def declared(self):
        return True

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __format_dict(self):
        return self.__impl


class MultiImplSpecDecl(SpecDecl):
    def __init__(self, name, filename=None, options=None):
        super().__init__(name)
        self.__filename = filename
        self.__options = options
        self.__implementations = {}

    def get_origin(self):
        return self.__filename

    def declare(self, filename, options=None):
        self.__filename = filename
        self.__options = options

    def declared(self):
        return self.__filename is not None

    def add_implementation(self, impl):
        name = impl['name']
        if name in self.__implementations:
            raise ValueError(
                'Multiple impementation {0} for declaration {1}'.format(
                    name, self.__name))
        self.__implementations[name] = impl

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __mkitem(self, name, content):
        content = copy.deepcopy(content)
        content.pop('name')
        content['@id'] = name
        content['@inherit'] = ['once', ]
        return content

    def __format_dict(self):
        uniq_items = [self.__mkitem(k, v)
                      for k, v in self.__implementations.items()]
        return {
            'name': self.name(),
            'entries': [
                {
                    '@id': self.name(),
                    '@inherit': ['once', ],
                    'uniq-items': uniq_items,
                }
            ]
        }


class FileScope(object):
    def __init__(self, name, entries):
        self.__name = name
        self.__entries = entries

    def name(self):
        return self.__name

    def __iter__(self):
        return iter(self.__entries)


class GlobalScope(dict):
    pass


class _Specs(object):
    def __init__(self):
        self.__specs = {}
        self.__global_scope = GlobalScope()
        self.__files = []
        self.__scan_files()
        self.__precompile_files()

    def __scan_files(self):
        cfg = common.config.Config()
        if not cfg.exists('/parser/specdefs'):
            return
        for d in cfg['/parser/specdefs']:
            self.__loaddir(d)

    def __loaddir(self, dirname):
        for f in os.listdir(dirname):
            fullname = os.path.join(dirname, f)
            if os.path.isdir(fullname):
                self.__loaddir(fullname)
            elif os.path.isfile(fullname) and fullname.endswith('.json'):
                self.__load_file(fullname)

    def __load_file(self, filename):
        mj = common.multijson.MultiJsonFile(filename)
        local_file_dicts = self.__combine_implementations(filename, mj.dicts())
        scope = FileScope(filename, local_file_dicts)
        self.__files.append(scope)

    def __combine_implementations(self, filename, dicts):
        res = []
        for j in dicts:
            if '@declare' in j:
                res.append(self.__declare(j['@declare'], filename))
            elif '@implement' in j:
                self.__add_implementation(j, filename)
            else:
                res.append(self.__declare_single(j, filename))
        return res

    def __declare(self, decl_name, filename, options=None):
        if options is None:
            options = {}

        declaration = self.__global_scope.get(decl_name)
        if declaration is None:
            declaration = MultiImplSpecDecl(decl_name, filename, options)
            self.__global_scope[decl_name] = declaration
        elif not declaration.declared():
            declaration.declare(filename, options=options)
        else:
            raise ValueError(
                'Duplicate declaration for spec {0}. Declared in {1}'.format(
                    decl_name, declaration.get_origin()
                )
            )
        return declaration

    def __declare_single(self, j, filename):
        decl_name = j['name']
        declaration = self.__global_scope.get(decl_name)
        if declaration is not None:
            raise ValueError(
                'Single-implementation for spec {0}. Declared in {1}'.format(
                    decl_name, declaration.get_origin()
                )
            )
        declaration = SingleImplSpecDecl(j, filename)
        self.__global_scope[decl_name] = declaration
        return declaration

    def __add_implementation(self, j, filename):
        decl_name = j.pop('@implement')
        o = self.__global_scope.get(decl_name)
        if o is None:
            o = MultiImplSpecDecl(decl_name, options=None)
            self.__global_scope[decl_name] = o

        o.add_implementation(j)

    def __precompile_files(self):
        for f in self.__files:
            self.__precompile_file(f)

    def __precompile_file(self, f):
        scope = PreprocessScope()
        for j in f:
            obj = j.format('dict')
            res = PreCompiler().compile(copy.deepcopy(obj), scope=scope)
            scope.add_specs(res, source=copy.deepcopy(obj))
            self.__add_specs(res)

    def __add_specs(self, specs):
        for s in specs:
            assert s.get_name() not in self.__specs
            self.__specs[s.get_name()] = s

    def __getitem__(self, index):
        return self.__specs[index]

    def __iter__(self):
        for v in self.__specs.values():
            yield v


@singleton
class PreCompiler(_PreCompiler):
    pass


@singleton
class Preprocessor(_Preprocessor):
    pass


@singleton
class Specs(_Specs):
    pass


def specs(name):
    return Specs()[name]
