#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import sys
import time
import argparse
from contextlib import contextmanager


import common.fake
import common.config
import common.output
import parser
import parser.io.export

import tests.compare


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

    res = parser.parse_args(sys.argv[1:])

    if res.test is None:
        if res.sentence is not None:
            res.option.append('/tests/parser/sentence={0}'.format(res.sentence))
        else:
            raise ValueError('neither sentence nor test file specified')

    if res.sentence is not None and res.test is not None:
        raise ValueError('only one option sentence or test is allowed')

    if res.test is not None:
        if not os.path.exists(res.test):
            raise ValueError('test path <{0}> not found'.format(res.test))
        if not os.path.isdir(res.test):
            raise ValueError('test path shall be directory')
        res.config.append(os.path.join(res.test, 'config/config.json'))

    if not res.config:
        raise ValueError('no config file provided')

    return res


def get_sentence(opts):
    cfg = parser.config()
    return cfg['/tests/parser/sentence']


def execute(opts):
    sentence = get_sentence(opts)

    with timeit_ctx('total'):
        print('Sentence: {0}'.format(sentence))
        print('Output: {0}'.format(common.output.defpath()))
        print()

        parser.io.export.generate(
            cfg_path='/parser/debug',
            config=[common.fake.named(parser.config(), 'config'), ]
        )

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

        if opts.test:
            with timeit_ctx('comparing results'):
                reference = tests.compare.from_fs(
                    os.path.join(opts.test, 'sequences')
                )
                cmpres = tests.compare.compare(reference, list(ctx_output))
                text_res = 'Test confirmed' if cmpres else 'Test failed'
            print(text_res)


if __name__ == '__main__':
    opts = parse_opts()
    parser.configure(filenames=opts.config, override_args=opts.option)

    execute(opts)
