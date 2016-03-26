#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sys
import os
import codecs
import time
import json
import unittest
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
    print('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)))


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


# def hfcn(n):
#     print (n['udata']['position'], n['udata']['word'])
#     return hash((n['udata']['position'], n['udata']['word']))


class MatchResComparator(common.dictcmp.GraphComparator):
    def __init__(self, reference, obj):
        super(MatchResComparator, self).__init__(
            reference,
            obj,
            lambda n:
                hash((n['udata']['position'], n['udata']['word']))
        )

    def compare(self):
        if not self.nodes_presence():
            return False
        if not self.linkage():
            return False
        return True
        # gc.nodes_equality()


class ParserTestCase(unittest.TestCase):
    def __init__(self, methodName='test_sentence', filename=None):
        assert filename is not None
        super(ParserTestCase, self).__init__(methodName)
        self.filename = filename

    def setUp(self):
        print ''
        with open(self.filename) as f:
            data = json.load(f)
            self.sentence = data['input']
            self.reference = data['graph']
        print u'Setting env for {0}'.format(self.sentence)
        with timeit_ctx('loading worddb'):
            self.tm = TokenMapper('./dbs/worddb.db')
        with timeit_ctx('building spec matcher'):
            self.srm = SequenceSpecMatcher(False)

    def test_sentence(self):
        with timeit_ctx('tokenizing'):
            tokens = parser.sentparser.Tokenizer().tokenize(self.sentence)

        with timeit_ctx('mapping word forms'):
            parsed_sentence = self.tm.map(tokens)

        with timeit_ctx('matching sentences'):
            matched_sentences = self.srm.match_sentence(parsed_sentence, most_complete=True)

        res = matched_sentences.export_obj()
        obj_res = res[0]
        obj_reference = self.reference[0]
        mrc = MatchResComparator(obj_reference, obj_res)
        self.assertTrue(mrc.compare())
        # print res_json

        for j, sq in enumerate(matched_sentences.get_sequences()):
            # sq.print_sequence()
            parser.graph.SequenceGraph(img_type='svg').generate(
                sq,
                oput.get_output_file('imgs', 'sq-{0}.svg'.format(j))
            )


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
            map(
                lambda f: os.path.join(parser_tests_dir, f),
                filter(
                    lambda f: f.endswith('.json'),
                    os.listdir(parser_tests_dir)
                )
            )
        )
    )

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
