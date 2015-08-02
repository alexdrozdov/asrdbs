#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.sentparser
import parser.graph
import parser.gvariant
import parser.specs
import sys
import codecs


sys.stdout = codecs.getwriter('utf8')(sys.stdout)


sentence = [u'падал', u'прошлогодний', u'снег', u'на', u'теплую', u'землю', u'поля']
sentence = [u'мелькнул', u'последний', u'луч', u'жаркого', u'дня']
sentence = [u'мелькнул', u'последний', u'яркий', u'луч', u'жаркого', u'дня']
sentence = [u'мелькнул', u'последний', u',', u'яркий', u'луч', u'жаркого', u'дня']
# sentence = [u'падал', u'прошлогодний', u'снег', u'на', u'теплую', u'землю', u',', u'поля']
# sentence = [u'падал', u'снег']
# sentence = [u'прошлогодний', u'снег']
# sentence = [u'она', u'летела']
# sentence = [u'на', u'поезд']
# sentence = [u'в', u'комнате']
# sentence = [u'на', u'солнце']
sentence = [u'полная', u'луна', u'плыла', u'на', u'темном', u'ночном', u'небе']
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
# sentence = [u'он', u'сидел', u'на', u'стволе', u'упавшего', u'дерева']
# sentence = [u'наши', u'дела', u'шли']
# sentence = [u'мы', u'поймали', u'его', u'в', u'парке']
# sentence = [u'красные', u'цветы']


sp = parser.sentparser.SentenceParser('./dbs/worddb.db')
res = sp.parse(sentence)

g = parser.graph.SentGraph(img_type='svg')
g.generate(res, 'imgs/g.svg')

gv = parser.gvariant.GraphSnakes()
snakes = gv.build(res)

for i in range(len(snakes)):
    snake = snakes[i]
    file_name = 'imgs/g-{0}.svg'.format(i+1)
    g.generate(res, file_name, snake)

graphs = gv.export_graphs()

# srm = parser.gvariant.SequenceRuleMatcher()
srm = parser.specs.SequenceSpecMatcher()
i = 0
for gr in graphs:
    print u"#" + str(i+1)
    gr.print_graph()
    sqs = srm.match_graph(gr)
    for sq in sqs:
        sq.print_sequence()
    print ''
    gr.apply_sequences()

    file_name = 'imgs/gr-{0}.svg'.format(i+1)
    g.generate(res, file_name, gr)

    i += 1

    srm.reset()
