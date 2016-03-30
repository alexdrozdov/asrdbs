#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sys
import os
import codecs
import time
import json
import unittest
import logging
from contextlib import contextmanager
import parser.sentparser
import parser.graph
import parser.graph_span
import parser.specs
import common.dictcmp
from common.output import output as oput

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

sentences = [
    # u'мальчики, девочки сидели на лавочке',
    u'мама мыла покрашенную раму',
    # u'падал прошлогодний снег на теплую землю поля',
    # u'мелькнул последний луч жаркого дня',
    # u'мелькнул последний яркий луч жаркого дня',
    # u'мелькнул последний , яркий луч жаркого дня',
    # u'хижина рыбака стояла на береге синего моря',
    # u'он сидел на стволе упавшего дерева',
    # u'мальчик сидел на стволе упавшего дерева',
    # u'наши дела шли',
    # u'мы поймали его в парке',
    # u'красные цветы',
]


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
                hash((n['udata']['position'], n['udata']['word'])),
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
    def __init__(self, methodName='test_sentence', filename=None):
        assert filename is not None
        super(ParserTestCase, self).__init__(methodName)
        self.filename = filename
        self.filename_base = os.path.splitext(os.path.basename(self.filename))[0]

    def setUp(self):
        print ''

    def test_sentence(self):
        with timeit_ctx('loading worddb'):
            self.tm = TokenMapper('./dbs/worddb.db')
        with timeit_ctx('building spec matcher'):
            self.srm = SequenceSpecMatcher(False)

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


def suite():
    parser_tests_dir = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)
        ),
        'parser'
    )
    return unittest.TestSuite(
        map(
            lambda filename: ParserTestCase(filename=filename),
            filter(
                lambda d: os.path.exists(d),
                map(
                    lambda e: os.path.join(parser_tests_dir, e, 'test.json'),
                    os.listdir(parser_tests_dir)
                )
            )
        )
    )

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    runner = unittest.TextTestRunner()
    runner.run(suite())
