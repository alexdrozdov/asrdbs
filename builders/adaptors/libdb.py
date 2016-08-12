#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import librudb.librudb
import librudb.base
import common.db


class LibrudbAdapter(object):
    def __init__(self, libdb_filename):
        self.__libdb_filename = libdb_filename

        if not os.path.exists(self.__libdb_filename):
            raise IOError('File ' + self.__libdb_filename + ' not found. Defered load will also fail')

        self.__text = None
        self.__words = None
        self.__words_pos = 0
        self.__text_pos = 0
        self.__libdb = None
        self.__iter = None

    def __load(self):
        print('Loading libdb ' + self.__libdb_filename + '...')
        self.__libdb = librudb.librudb.Librudb(self.__libdb_filename)
        self.__iter = common.db.DbRoIterator(self.__libdb, 'lib', ['text_id', 'path', 'md5', 'content'])

    def has_data(self):
        if self.__libdb is None:
            self.__load()
        return self.__iter.has_data()

    def get(self, count=1):
        if self.__libdb is None:
            self.__load()
        res = []
        for r in self.__iter.get(count):
            text_id, path, md5, content = r
            lt = librudb.base.LibruText(text_id, path, md5, content)
            res.append(lt)
        return res


class LibrudbWordsAdapter(object):
    def __init__(self, libdb_filename):
        self.__libdb_filename = libdb_filename

        if not os.path.exists(self.__libdb_filename):
            raise IOError('File ' + self.__libdb_filename + ' not found. Defered load will also fail')

        self.__libdb_adapt = None
        self.__words = None
        self.__len = None
        self.__pos = 0

    def __load(self):
        self.__libdb_adapt = LibrudbAdapter(self.__libdb_filename)
        if self.__libdb_adapt.has_data():
            self.__get_next_text()

    def __get_next_text(self):
        lt = self.__libdb_adapt.get(1)[0]
        txt = lt.get_content()
        print("Processing", lt.get_path())

        unwanted_chars = '*+-()@#№%^&_{}[]"\'/\\<>~=,.:;!?\r\n'
        tt = {ord(c): ord(' ') for c in unwanted_chars}
        self.__words = txt.translate(tt).strip().split()
        self.__len = len(self.__words)
        self.__pos = 0

    def has_data(self):
        if self.__libdb_adapt is None:
            self.__load()
        return self.__pos < self.__len or self.__libdb_adapt.has_data()

    def get(self, count=1):
        if self.__libdb_adapt is None:
            self.__load()
        res = []

        if self.__pos < self.__len:
            res = self.__words[self.__pos:self.__pos+count]
            self.__pos += len(res)
            if len(res) == count:
                return res

        if self.__libdb_adapt.has_data():
            self.__get_next_text()
            res.extend(self.__words[self.__pos:self.__pos+count])
            self.__pos += len(res)
        return res
