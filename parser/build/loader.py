#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.lang.base.at
import parser.build.jsonspecs
import parser.build.preprocessor
import parser.build.compiler
import parser.engine.rt
import parser.io.export
import common.dg
from argparse import Namespace as ns
from common.singleton import singleton


class Engine(object):
    def __init__(self, specs, matchers, primary):
        self.__specs = specs
        self.__matchers = matchers
        self.__primary = primary

    def get_spec(self, base_spec_name):
        return self.__specs[base_spec_name].base_spec_class

    def get_matcher(self, name, none_on_missing=False):
        if none_on_missing:
            return self.__matchers.get(name)
        return self.__matchers[name]

    def get_primary(self):
        return self.__primary

    def new_context(self):
        event_listener = parser.engine.rt.ContextOutputDispatcher()
        event_forwarder = parser.engine.rt.ContextEventsForwarder(event_listener)
        ctx_callbacks = MatcherCallbacks(self)
        top_spec_matcher = parser.engine.rt.TopSpecMatcher()

        intctx = parser.engine.rt.MatcherContext(
            top_spec_matcher, event_listener, ctx_callbacks
        )
        for m in self.get_primary():
            intctx.create_ctx(m.get_name(), event_listener=event_forwarder)

        return parser.engine.rt.Context(intctx, event_listener)


class MatcherCallbacks(object):
    def __init__(self, compiled):
        self.__compiled = compiled

    def find_matcher(self, name, none_on_missing=False):
        return self.__compiled.get_matcher(
            name, none_on_missing=none_on_missing)


class LoaderImpl(object):
    def __init__(self):
        self.__primary_spec = None
        self.__matchers = []
        self.__primary = []
        self.__spec_by_name = {}
        self.__matcher_by_name = {}
        self.__preprocessor = parser.build.preprocessor.Preprocessor()

    def load(self, primary=None):
        if primary is None:
            cfg = common.config.Config()
            primary = cfg['/parser/primary']

        assert primary is not None

        self.__primary_spec = primary
        self.__primary = []
        self.__create_specs()
        return Engine(
            self.__spec_by_name, self.__matcher_by_name, self.__primary)

    def __create_specs(self):
        for sd in parser.build.jsonspecs.Specs():
            self.__add_spec(sd)
        self.__generate_src_debug()
        self.__build_specs()
        self.__generate_selectors_debug()
        self.__generate_structure_debug()

    def __is_primary(self, name):
        return name == self.__primary_spec

    def __add_spec(self, base_spec_class):
        if base_spec_class.get_name() in self.__spec_by_name:
            return

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
            if spec_name in self.__matcher_by_name:
                continue
            if self.__is_primary(spec_name):
                self.__build_spec(spec_name)

    def get_spec(self, base_spec_name):
        return self.__spec_by_name[base_spec_name].base_spec_class

    def get_matcher(self, name, none_on_missing=False):
        if none_on_missing:
            return self.__matcher_by_name.get(name)
        return self.__matcher_by_name[name]

    def get_primary(self):
        return self.__primary

    def __generate_src_debug(self):
        parser.io.export.generate(
            cfg_path='/parser/debug',
            src=parser.build.jsonspecs.Specs()
        )

    def __generate_selectors_debug(self):
        parser.io.export.generate(
            cfg_path='/parser/debug',
            selectors=(
                common.dg.Subgraph.from_node(n)
                for n in parser.spare.selectors.Selectors()
            ),
        )

    def __generate_structure_debug(self):
        parser.io.export.generate(
            cfg_path='/parser/debug',
            structure=(m.get_compiled_spec() for m in self.__matchers)
        )


@singleton
class Loader(LoaderImpl):
    pass


def new_engine(primary=None):
    loader = Loader()
    return loader.load(primary=primary)
