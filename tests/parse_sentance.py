#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.sentparser
import parser.graph
import parser.graph_span
import parser.specs
import sys
import codecs
import time
from contextlib import contextmanager
from common.output import output as oput

sys.stdout = codecs.getwriter('utf8')(sys.stdout)


@contextmanager
def timeit_ctx(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    print('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)))


sentence = [u'падал', u'прошлогодний', u'снег', u'на', u'теплую', u'землю', u'поля']
# sentence = [u'мелькнул', u'последний', u'луч', u'жаркого', u'дня']
# sentence = [u'мелькнул', u'последний', u'яркий', u'луч', u'жаркого', u'дня']
# sentence = [u'мелькнул', u'последний', u',', u'яркий', u'луч', u'жаркого', u'дня']
# sentence = [u'падал', u'прошлогодний', u'снег', u'на', u'теплую', u'землю', u',', u'поля']
# sentence = [u'падал', u'снег']
# sentence = [u'прошлогодний', u'снег']
# sentence = [u'она', u'летела']
# sentence = [u'на', u'поезд']
# sentence = [u'в', u'комнате']
# sentence = [u'на', u'солнце']
# sentence = [u'полная', u'луна', u'медленно', u'плыла', u'на', u'темном', u'ночном', u'небе']
sentence = [u'полная', u'луна', u'медленно', u'плыла', u'на', u'темном', u'ночном', u'небе']
sentence = [u'друзья', u'быстро', u'шли', u'по', u'зеленым', u'лугам', u',', u'бескрайним', u'полям']
sentence = [u'друзья', u'шли', u'по', u'зеленым', u'лугам', u'бескрайним', u'полям']
# sentence = [u'мои', u'друзья', u'гуляли']
# sentence = [u'его', u'друзья', u'гуляли']
# sentence = [u'наши', u'друзья', u'гуляли']
# sentence = [u'их', u'друзья', u'гуляли']
# sentence = [u'его', u'и', u'ее',  u'друзья', u'гуляли']
# sentence = [u'его', u'и', u'ее',  u'друзья', u'пришли', u'на', u'его', u'день', u'рождения']
# sentence = [u'друзья', u'быстро', u'шли', u'по', u'зеленым', u'лугам', u',', u'бескрайним', u'полям', u'огромной', u'страны']
# sentence = [u'верные', u'друзья', u'быстро', u'шли', u'по', u'зеленым', u'лугам', u',', u'бескрайним', u'полям', u'огромной', u'страны']
# sentence = [u'зеленым', u'лугам', u'бескрайним', u'полям']
# sentence = [u'луна', u'сияла', u'на', u'темном', u'ночном', u'небе']
# sentence = [u'холод', u'зимы']
# sentence = [u'медленно', u'падал', u'мокрый', u'снег', u'на', u'землю']
# sentence = [u'он', u'нашел', u'формулу', u'философского', u'камня']
# sentence = [u'его', u'следы', u'нашлись', u'в', u'далекой', u'стране']
# sentence = [u'мое', u'время', u'текло', u'невероятно', u'быстро']
# sentence = [u'на', u'небе', u'восходило', u'ярко', u'красное', u'солнце']
# sentence = [u'в', u'весеннем', u'саду', u'цвели', u'ярко', u'красные', u'тюльпаны', u'нежно', u'белые', u'нарциссы', ]
# sentence = [u'в', u'весеннем', u'саде', u'цвели', u'ярко', u'красные', u'тюльпаны']
# sentence = [u'в', u'весеннем', u'саде', u'у', u'дома', u'цвели', u'ярко', u'красные', u'тюльпаны']
# sentence = [u'в', u'весеннем', u'саде', u'у', u'моего', u'дома', u'цвели', u'ярко', u'красные', u'тюльпаны']
# sentence = [u'на', u'береге', u'синего', u'моря', u'стояла', u'хижина', u'рыбака']
# sentence = [u'хижина', u'рыбака', u'стояла', u'на', u'береге', u'синего', u'моря']
# sentence = [u'он', u'сидел', u'на', u'стволе', u'упавшего', u'дерева']
# sentence = [u'мальчик', u'сидел', u'на', u'стволе', u'упавшего', u'дерева']
# sentence = [u'наши', u'дела', u'шли']
# sentence = [u'мы', u'поймали', u'его', u'в', u'парке']
# sentence = [u'красные', u'цветы']
# sentence = [u'мальчики', u'и', u'девочки', u'сидели', u'на', u'лавочке']
sentence = [u'мальчики', u',', u'девочки', u'сидели', u'на', u'лавочке']
sentence = u'мама мыла покрашенную раму'
# sentence = [u'мама', u'мыла', u'покрашенную', u'белой', u'краской', u'раму', u'окна']
# sentence = [u'я', u'смотрел', u'на', u'березу', u',', u'стоящую', u'под', u'окном', u',', u'покрытую', u'снегом']
# sentence = [u'косой', u'косой', u'косил', u'косой', u'косой']
# sentence = u'ярко красный'

with timeit_ctx('total'):
    with timeit_ctx('loading database'):
        tm = parser.sentparser.TokenMapper('./dbs/worddb.db')
    with timeit_ctx('building parser'):
        srm = parser.specs.SequenceSpecMatcher(False)

    with timeit_ctx('tokenizing'):
        tokens = parser.sentparser.Tokenizer().tokenize(sentence)

    with timeit_ctx('mapping word forms'):
        parsed_sentence = tm.map(tokens)

    with timeit_ctx('matching sentences'):
        matched_sentences = srm.match_sentence(parsed_sentence, most_complete=False)

    for j, sq in enumerate(matched_sentences.get_sequences()):
        sq.print_sequence()
        parser.graph.SequenceGraph(img_type='svg').generate(
            sq,
            oput.get_output_file('imgs', 'sq-{0}.svg'.format(j))
        )
