#!/usr/bin/env python
# -*- coding: utf-8 -*-

import worddb.builders
import adaptors.odict


wdd = worddb.builders.WorddbBuilder('./worddb1.db')
odict_adapt = adaptors.odict.OdictAdapter('o_dict.pickle')
wdd.add_words(odict_adapt)
