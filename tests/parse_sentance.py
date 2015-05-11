#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.sentparser
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
# sentence = [u'луна', u'светила', u'на', u'ночном', u'небе']
sentence = [u'холод', u'зимы']

sp = parser.sentparser.SentenceParser('./dbs/worddb.db')
sp.parse(sentence)
