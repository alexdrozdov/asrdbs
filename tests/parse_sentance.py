#!/usr/bin/env python
# -*- #coding: utf8 -*-


import parser.sentparser

sentence = [u'падал', u'прошлогодний', u'снег', u'на', u'теплую', u'землю', u'поля']

sp = parser.sentparser.SentenceParser('./dbs/worddb.db')
sp.parse(sentence)
