#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sys
import os
import codecs
import time
import json
import unittest
import logging
import argparse
from contextlib import contextmanager
import common.config
import parser.sentparser
import parser.graph
import parser.graph_span
import parser.specs
import common.dictcmp
from common.output import output as oput

sys.stdout = codecs.getwriter('utf8')(sys.stdout)


@contextmanager
def timeit_ctx(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    logging.info('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)))


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class TokenMapper(parser.sentparser.TokenMapper):
    pass


@singleton
class SequenceSpecMatcher(parser.specs.SequenceSpecMatcher):
    pass


class MatchResCmp(common.dictcmp.GraphCmp):
    def __init__(self, d):
        super(MatchResCmp, self).__init__(
            d,
            lambda n:
                hash((
                    n['udata']['position'],
                    n['udata']['word'],
                    n['udata']['name'] if n['udata'].has_key('virtual') and n['udata']['virtual'] else '',
                )),
            lambda n:
                not n['udata']['hidden'],
            [
                '/udata/form/count',
                '/udata/form/case',
                '/udata/form/animation',
                '/udata/form/parts_of_speech',
                '/udata/verb_form',
                '/udata/time'
                '/udata/hidden',
                '/udata/anchor']
        )

    def __eq__(self, other):
        if not isinstance(other, MatchResCmp):
            other = MatchResCmp(other)
        return super(MatchResCmp, self).__eq__(other)


class CrossMatchResCmp(object):
    def __init__(self, obj):
        assert isinstance(obj, list)
        self.__obj = obj
        self.__cmps = map(
            lambda o:
                MatchResCmp(o),
            self.__obj
        )

    def __eq__(self, other):
        if not isinstance(other, CrossMatchResCmp):
            other = CrossMatchResCmp(other)
        if len(self.__obj) != len(other.__obj):
            return False
        for i, c in enumerate(self.__cmps):
            for j, cc in enumerate(other.__cmps):
                if c == cc:
                    break
            else:
                return False
            continue
        return True


class ParserTestCase(unittest.TestCase):
    def __init__(self, methodName='test_sentence', filename=None, primary='sentence'):
        assert filename is not None
        super(ParserTestCase, self).__init__(methodName)
        self.filename = filename
        self.filename_base = os.path.splitext(os.path.basename(self.filename))[0]
        self.primary = primary

    def setUp(self):
        print ''

    def test_sentence(self):
        with timeit_ctx('loading worddb'):
            self.tm = TokenMapper('./dbs/worddb.db')
        with timeit_ctx('building spec matcher'):
            self.srm = SequenceSpecMatcher(False, primary=self.primary)

        with open(self.filename) as f:
            data = json.load(f)
            self.sentence = data['input']
            self.reference = data['graph']
        logging.info(u'Setting env for {0}'.format(self.sentence))

        with timeit_ctx('tokenizing'):
            tokens = parser.sentparser.Tokenizer().tokenize(self.sentence)

        with timeit_ctx('mapping word forms'):
            parsed_sentence = self.tm.map(tokens)

        with timeit_ctx('matching sentences'):
            matched_sentences = self.srm.match_sentence(
                parsed_sentence,
                most_complete=True
            )

        with timeit_ctx('comparing with reference'):
            obj_res = matched_sentences.export_obj()
            res = CrossMatchResCmp(self.reference) == obj_res

        if not res:
            with timeit_ctx('exporting failed test result'):
                for j, sq in enumerate(matched_sentences.get_sequences()):
                    parser.graph.SequenceGraph(img_type='svg').generate(
                        sq,
                        oput.get_output_file(
                            [self.filename_base, 'imgs'],
                            'sq-{0}.svg'.format(j)
                        )
                    )
                with open(
                    oput.get_output_file(self.filename_base, 'res.json'),
                    'w'
                ) as jf:
                    json.dump(
                        {
                            'input': self.sentence,
                            'expected': self.reference,
                            'graph': obj_res
                        },
                        jf
                    )

        self.assertTrue(res)


def suite(parser_tests_dir, primary):
    return unittest.TestSuite(
        map(
            lambda filename: ParserTestCase(filename=filename, primary=primary),
            filter(
                lambda d: os.path.exists(d),
                map(
                    lambda e: os.path.join(parser_tests_dir, e, 'test.json'),
                    os.listdir(parser_tests_dir)
                )
            )
        )
    )


def parse_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--test-dir')
    res = parser.parse_args(sys.argv[1:])

    if res.test_dir is None:
        raise ValueError('test directory required')

    return res


if __name__ == '__main__':
    opts = parse_opts()
    cfg = common.config.Config(filename=os.path.join(opts.test_dir, 'config.json'))

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    runner = unittest.TextTestRunner()
    runner.run(suite(opts.test_dir, cfg['/tests/primary']))
