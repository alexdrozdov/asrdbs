#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import pickle


class OdictAdapter(object):
    def __init__(self, odict_filename):
        self.__odict_filename = odict_filename

        if not os.path.exists(self.__odict_filename):
            raise IOError('File ' + self.__odict_filename + ' not found. Defered load will also fail')

        self.__odict = None
        self.__len = None
        self.__pos = 0

    def __load(self):
        print 'Loading odict ' + self.__odict_filename + '...'
        with open(self.__odict_filename) as f:
            self.__odict = pickle.load(f)
            self.__len = len(self.__odict)

    def has_data(self):
        if self.__odict is None:
            self.__load()
        return self.__pos < self.__len

    def get(self, count=1):
        if self.__odict is None:
            self.__load()
        count = min(count, self.__len - self.__pos)
        words = self.__odict[self.__pos:self.__pos+count]
        self.__pos += count
        return words
