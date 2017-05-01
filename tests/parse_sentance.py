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


@contextmanager
def timeit_ctx(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    print(('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000))))


def parse_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sentence')
    parser.add_argument('-t', '--test')
    parser.add_argument('-p', '--primary')
    parser.add_argument('-m', '--make-test', action='store_true', default=False)
    parser.add_argument(
        '-b', '--build-only',
        action='store_true', default=False
    )
    parser.add_argument('--no-structure', action='store_true', default=False)
    parser.add_argument('--no-selectors', action='store_true', default=False)
    parser.add_argument('--no-database', action='store_true', default=False)
    res = parser.parse_args(sys.argv[1:])

    if res.sentence is None and res.test is None:
        raise ValueError('neither sentence nor test file specified')

    if res.sentence is not None and res.test is not None:
        raise ValueError('only one option sentence or test is allowed')

    if res.test is not None and not os.path.exists(res.test):
        raise ValueError('test file <{0}> not found'.format(res.test))

    return res


def execute(opts):
    if opts.sentence is not None:
        sentence = opts.sentence
    elif opts.test is not None:
        with open(opts.test) as f:
            data = json.load(f)
            sentence = data['input']

    with timeit_ctx('total'):
        if not opts.no_database:
            with timeit_ctx('loading database'):
                parser.TokenMapper('./dbs/worddb.db')
        with timeit_ctx('building parser'):
            prs = parser.Loader(
                primary=opts.primary,
                structure=not opts.no_structure,
                selectors=not opts.no_selectors
            )
        with timeit_ctx('constructing matcher'):
            srm = parser.Matcher(prs)

        if not opts.build_only:
            with timeit_ctx('constructing sentence'):
                tokenized_sentence = parser.api.Sentence.from_sentence(sentence)

            ctx = srm.new_context()
            ctx.push_sentence(tokenized_sentence)

            with timeit_ctx('matching sentences'):
                matched_sentences = srm.process(ctx)

            with timeit_ctx('exporting results'):
                parser.io.export.generate(
                    cfg_path='/parser/debug',
                    sequences=(common.fake.named(sq, i)
                               for i, sq in enumerate(matched_sentences))
                )


if __name__ == '__main__':
    cfg = common.config.Config(
        obj={
            'app': {
                'modules': [
                    'parser',
                    'worddb',
                ],
            },
            'parser': {
                'compiler': {
                    'max-static-include-level': 1,
                    'force-static-include': False,
                    'force-dynamic-include': False
                },
                'specdefs': ['parser/volume/ru_RU/structure', ],
                'linkdefs': ['ru_RU/enchanced/linkdefs', ],
                'selectors': ['parser/volume/ru_RU/selectors', ],
                'templates': [
                    'parser/templates',
                    'parser/lang/ru_RU/enchanced/templates/selectors'
                ],
                'props': ['parser/volume/ru_RU/properties', ],
                'io': {
                    'jinja2': {
                        'templates': ['parser/volume/io/jinja2/templates', ],
                        'styles': 'parser/volume/io/jinja2/styles',
                        'fmtmap': {
                            'graph': 'graph.dot.tmpl'
                        }
                    }
                },
                'debug': {
                    'src': {
                        'svg': False,
                        'json': True,
                        'path': 'preprocessor'
                    },
                    'structure': {
                        'svg': False,
                        'json': False,
                        'path': 'structure'
                    },
                    'selectors': {
                        'svg': False,
                        'json': False,
                        'path': 'selectors'
                    },
                    'sequences': {
                        'svg': True,
                        'json': True,
                        'str': True,
                        'path': 'sequences'
                    }
                }
            },
        }
    )

    opts = parse_opts()
    execute(opts)
