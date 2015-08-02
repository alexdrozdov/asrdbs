#!/usr/bin/env python
# -*- #coding: utf8 -*-


import data.extend_prepositional
import adaptors.wordtxt


epc = data.extend_prepositional.ExtPreposionalCase('./data/morh2.txt')
wdtxt = adaptors.wordtxt.WordtxtAdapter('./data/morh.txt')
epc.add_words(wdtxt)
