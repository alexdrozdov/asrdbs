#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.sentparser
import parser.graph
import parser.gvariant
import sys
import codecs


sys.stdout = codecs.getwriter('utf8')(sys.stdout)


# sentence = [u'падал', u'прошлогодний', u'снег', u'на', u'теплую', u'землю', u'поля']
# sentence = [u'падал', u'снег']
# sentence = [u'прошлогодний', u'снег']
# sentence = [u'она', u'летела']
# sentence = [u'на', u'поезд']
# sentence = [u'в', u'комнате']
# sentence = [u'на', u'солнце']
sentence = [u'луна', u'светила', u'на', u'темном', u'ночном', u'небе']
# sentence = [u'холод', u'зимы']
# sentence = [u'падал', u'мокрый', u'снег', u'на', u'землю']

sp = parser.sentparser.SentenceParser('./dbs/worddb.db')
res = sp.parse(sentence)

g = parser.graph.SentGraph(img_type='png')
g.generate(res, 'imgs/g.png')

gv = parser.gvariant.GraphSnakes()
snakes = gv.build(res)

for i in range(len(snakes)):
    snake = snakes[i]
    file_name = 'imgs/g-{0}.png'.format(i+1)
    g.generate(res, file_name, snake)
