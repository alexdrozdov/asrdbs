#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.graph
import common.config
import parser.build.jsonspecs
import parser.build.preprocessor
import parser.build.compiler
import parser.engine.rt
from argparse import Namespace as ns


class Loader(object):
    def __init__(self, primary=None):
        self.__primary_spec = 'sentence' if primary is None else primary
        self.__matchers = []
        self.__primary = []
        self.__spec_by_name = {}
        self.__matcher_by_name = {}
        self.__preprocessor = parser.build.preprocessor.Preprocessor()
        self.__load_linkdefs()
        self.__create_specs()

    def __load_linkdefs(self):
        parser.matcher.load()

    def __load_module(self, path):
        parts = ['parser', 'lang'] + path.split('/')
        root = parts[0]
        parts = parts[1:]
        path = root
        obj = __import__(root, globals(), locals(), root)
        for p in parts:
            path += '.' + p
            obj = __import__(path, globals(), locals(), p)
        return obj

    def __create_specs(self):
        cfg = common.config.Config()
        for sd in parser.build.jsonspecs.Specs():
            self.__add_spec(sd)
        self.__build_specs()
        export_svg = cfg['/parser/export-svg']
        if export_svg is not None and export_svg:
            self.__export_svg()

    def __is_primary(self, name):
        return name == self.__primary_spec

    def __add_spec(self, base_spec_class):
        assert base_spec_class.get_name() not in self.__spec_by_name
        res = self.__preprocessor.preprocess(base_spec_class)
        self.__spec_by_name[base_spec_class.get_name()] = ns(
            base_spec_class=base_spec_class,
            matcher=None,
            dependencies=res.dependencies
        )

    def __build_spec(self, name):
        desc = self.__spec_by_name[name]
        if desc.matcher is not None:
            return
        desc.matcher = "Build in progress"
        for d in desc.dependencies:
            self.__build_spec(d)

        sc = parser.build.compiler.SpecCompiler(self)
        spec = sc.compile(desc.base_spec_class)
        matcher = parser.engine.rt.SpecMatcher(self, spec)
        desc.matcher = matcher
        self.__matchers.append(matcher)
        self.__matcher_by_name[matcher.get_name()] = matcher
        if self.__is_primary(matcher.get_name()):
            self.__primary.append(matcher)

    def __build_specs(self):
        for spec_name in list(self.__spec_by_name.keys()):
            if self.__is_primary(spec_name):
                self.__build_spec(spec_name)

    def get_spec(self, base_spec_name):
        return self.__spec_by_name[base_spec_name].base_spec_class

    def get_matcher(self, name):
        return self.__matcher_by_name[name]

    def get_primary(self):
        return self.__primary

    def export_svg(self):
        for sp in self.__matchers:
            g = parser.graph.SpecGraph(img_type='svg')
            spec_name = sp.get_name()
            file_name = common.output.output.get_output_file(
                'specs',
                '{0}.svg'.format(spec_name)
            )
            g.generate(sp.get_compiled_spec().get_states(), file_name)
