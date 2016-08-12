#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
import worddb.worddb
import common.db


class WorddbBlobsAdapter(object):
    def __init__(self, worddb_filename):
        self.__worddb_filename = worddb_filename

        if not os.path.exists(self.__worddb_filename):
            raise IOError('File ' + self.__worddb_filename + ' not found. Defered load will also fail')

        self.__worddb = None
        self.__iter = None

    def __load(self):
        print('Loading worddb ' + self.__worddb_filename + '...')
        self.__worddb = worddb.worddb.Worddb(self.__worddb_filename)
        self.__iter = common.db.DbRoIterator(self.__worddb, 'word_blobs', ['word', 'blob'])

    def has_data(self):
        if self.__worddb is None:
            self.__load()
        return self.__iter.has_data()

    def get(self, count=1):
        if self.__worddb is None:
            self.__load()
        return self.__iter.get(count)


class WorddbUnpackedBlobsAdapter(WorddbBlobsAdapter):
    def __init__(self, worddb_filename):
        WorddbBlobsAdapter.__init__(self, worddb_filename)

    def get(self, count=1):
        res = []
        for r in WorddbBlobsAdapter.get(self, count):
            word, blob = r
            res.apend((word, json.loads(blob)))
        return res
