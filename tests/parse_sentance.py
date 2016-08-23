#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import sys
import time
import json
import io
import argparse
import uuid
import common.config
import parser.api
import parser.graph
import parser.specs
import parser.selectors
from contextlib import contextmanager
from common.output import output as oput


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
        with timeit_ctx('loading database'):
            tm = parser.api.TokenMapper('./dbs/worddb.db')
        with timeit_ctx('building parser'):
            srm = parser.specs.SequenceSpecMatcher(primary=opts.primary)

        base_dir = str(uuid.uuid1()) if opts.make_test else None
        with timeit_ctx('dumping selectos'):
            parser.graph.SelectorGraph(img_type='svg').generate(
                parser.selectors.Selectors(),
                oput.get_output_file([base_dir, 'imgs'], 'selector-{0}.svg'.format(0))
            )

        with timeit_ctx('tokenizing'):
            tokens = parser.api.Tokenizer().tokenize(sentence)

        with timeit_ctx('mapping word forms'):
            parsed_sentence = tm.map(tokens)

        with timeit_ctx('matching sentences'):
            matched_sentences = srm.match_sentence(parsed_sentence, most_complete=True)

        for j, sq in enumerate(matched_sentences.get_sequences()):
            print(sq.format('str'))
            parser.graph.SequenceGraph(img_type='svg').generate(
                sq,
                oput.get_output_file([base_dir, 'imgs'], 'sq-{0}.svg'.format(j))
            )

        jf_name = 'test.json' if opts.make_test else 'res.json'
        with io.open(
            oput.get_output_file([base_dir, ''], jf_name), 'w', encoding='utf8'
        ) as jf:
            s = json.dumps(
                {
                    'input': sentence,
                    'graph': matched_sentences.export_obj()
                },
                jf,
                ensure_ascii=False
            )
            jf.write(s)


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
                'specdefs': ['ru_RU/enchanced/specdefs', ],
                'linkdefs': ['ru_RU/enchanced/linkdefs', ],
                'selectors': ['parser/lang/ru_RU/enchanced/selectors', ],
                'templates': [
                    'parser/templates',
                    'parser/lang/ru_RU/enchanced/templates/selectors'
                ],
                'props': ['parser/lang/ru_RU/enchanced/properties', ],
                'generate-svg': False
            },
        }
    )

    opts = parse_opts()
    execute(opts)
