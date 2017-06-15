#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import sys
import time
import json
import argparse
from contextlib import contextmanager


import common.fake
import common.config
import parser
import parser.io.export


def test_res(ctx):
    return parser.io.output_chain(
        ctx,
        parser.io.output.ToMatchedSequence,
        parser.io.output.MostComplete,
        parser.io.output.IgnoreDuplicate,
        parser.io.output.Store
    )


@contextmanager
def timeit_ctx(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    print(('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000))))


def parse_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', action='append', default=[])
    parser.add_argument('-o', '--option', action='append', default=[])

    parser.add_argument('-s', '--sentence')
    parser.add_argument('-t', '--test')
    parser.add_argument('-m', '--make-test', action='store_true', default=False)

    res = parser.parse_args(sys.argv[1:])

    if not res.config:
        raise ValueError('no config file provided')

    if res.sentence is None and res.test is None:
        raise ValueError('neither sentence nor test file specified')

    if res.sentence is not None and res.test is not None:
        raise ValueError('only one option sentence or test is allowed')

    if res.test is not None and not os.path.exists(res.test):
        raise ValueError('test file <{0}> not found'.format(res.test))

    return res


def get_sentence(opts):
    if opts.sentence is not None:
        sentence = opts.sentence
    elif opts.test is not None:
        with open(opts.test) as f:
            data = json.load(f)
            sentence = data['input']
    return sentence


def execute(opts):
    sentence = get_sentence(opts)

    with timeit_ctx('total'):
        with timeit_ctx('building engine'):
            engine = parser.new_engine()

        ctx = engine.new_context()
        ctx_input = parser.io.input_sentence(ctx)
        ctx_output = test_res(ctx)

        ctx_input.push(sentence)

        with timeit_ctx('matching sentences'):
            ctx.run_until_complete()

        with timeit_ctx('exporting results'):
            parser.io.export.generate(
                cfg_path='/parser/debug',
                sequences=(common.fake.named(sq, i)
                           for i, sq in enumerate(ctx_output))
            )


if __name__ == '__main__':
    opts = parse_opts()
    parser.configure(filenames=opts.config, override_args=opts.option)

    execute(opts)
