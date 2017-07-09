#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.spare.wordform
import parser.build.compiler
import parser.engine.sequence
import parser.engine.context


from argparse import Namespace as ns
from parser.engine.structs import TransitionAttempt


class SequenceCloner(object):
    def __init__(self, c_out_ctx, obj):
        self.__c_out = c_out_ctx
        self.__obj = obj
        self.__obj_used = False

    def get(self):
        obj = self.__obj
        if self.__obj_used:
            obj = obj.clone()
        self.__obj_used = True
        self.__c_out.checkout_sequence(obj)
        return obj


class AggregatedCtxTransitions(list):
    def __init__(self):
        super().__init__()
        self.__probabilities = []

    def append(self, v):
        super().append(v)
        self.__probabilities.extend([t.probability for t in v.transitions])

    def probabilities(self):
        return sorted(self.__probabilities)


class SpecMatcher(object):
    def __init__(self, owner, compiled_spec):
        assert owner is not None
        assert isinstance(compiled_spec, parser.build.compiler.CompiledSpec)
        self.__owner = owner
        self.__compiled_spec = compiled_spec
        self.__name = self.__compiled_spec.get_name()

    def is_applicable(self, form):
        return self.__compiled_spec.is_applicable(form)

    def match(self, ctx):
        self.__handle_sequences(ctx)
        return ns(complete=ctx.empty())

    def once(self, ctx):
        self.__handle_sequences(ctx)

    def __handle_sequences(self, ctx):
        if ctx.is_blank():
            parser.engine.sequence.new_sequence(self.__compiled_spec, self, ctx)

        while ctx.has_backlog():
            c_out = ctx.checkout_sequences()
            to_execute = self.__find_executables(c_out)
            self.__execute_sequences(c_out, to_execute)

            c_out.commit()

            if not ctx.has_backlog() and ctx.has_frozen():
                ctx.unfreeze_one()

        return ns(complete=ctx.empty())

    def __execute_sequences(self, c_out, to_execute):
        for ta in to_execute:
            res = ta.sq.follow(ta.trs)

            if not res.valid:
                c_out.fail_sequence(ta.sq)
                continue

            if res.fini:
                c_out.complete_sequence(ta.sq)
                continue

            if res.wait:
                c_out.ignore_sequence(ta.sq)
                c_out.wait_sequence(res.sq)
                continue

            c_out.confirm_sequence(ta.sq)

    def __deduce_min_probability(self, probabilities):
        best = probabilities[-1]
        for i in range(len(probabilities) - 1, -1, -1):
            p = probabilities[i]
            if p <= parser.engine.sequence.RtMatchSequence.dynamic_trs_fine:
                break
            best = p
        return best

    def __find_executables(self, c_out):
        sequences = c_out.sequences()

        agg_transitions = AggregatedCtxTransitions()
        for sq in sequences:
            agg_transitions.append(sq.fetch_transitions())

        probabilities = agg_transitions.probabilities()
        if not probabilities:
            return []
        min_probability = self.__deduce_min_probability(probabilities)

        to_execute = []
        for tps in agg_transitions:
            sq_cloner = SequenceCloner(c_out, tps.sq)
            frozen = None
            for trs in tps.transitions:
                if min_probability <= trs.probability:
                    ta = TransitionAttempt(
                        sq=sq_cloner.get(),
                        trs=trs
                    )
                    to_execute.append(ta)
                else:
                    if frozen is None:
                        frozen = parser.engine.sequence.FrozenSequence(
                            sq_cloner.get()
                        )
                        c_out.freeze(frozen)
                    frozen.append(trs)
        return to_execute

    def create_ctx(self, event_listener, owner=None):
        return parser.engine.context.create_ctx(self, event_listener, owner)

    def get_name(self):
        return self.__name

    def get_compiled_spec(self):
        return self.__compiled_spec


class TopSpecMatcher(object):
    def match(self, ctx):
        c_out = ctx.checkout_contexts()
        exe = self.__find_executables(c_out)
        for c in exe:
            c_out.checkout(c)
            res = self.__handle_ctx(c)
            if res.complete:
                c_out.complete(c)
            else:
                c_out.confirm(c)
        c_out.commit()

    def get_name(self):
        return 'root-ctx'

    def __find_executables(self, c_out):
        return [c for c in c_out.ctxs() if c.has_backlog()]

    def __handle_ctx(self, ctx):
        while True:
            c_out = ctx.checkout_contexts()
            exe = self.__find_executables(c_out)
            for c in exe:
                c_out.checkout(c)
                res = self.__handle_ctx(c)
                if res.complete:
                    c_out.complete(c)
                else:
                    c_out.confirm(c)
            c_out.commit()
            res = ctx.run_until_complete()
            if ctx.empty():
                break
        return res
