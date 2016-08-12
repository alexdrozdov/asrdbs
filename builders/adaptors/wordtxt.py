#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os


class WordtxtAdapter(object):
    def __init__(self, wordtxt_filename):
        self.__wordtxt_filename = wordtxt_filename

        if not os.path.exists(self.__wordtxt_filename):
            raise IOError('File ' + self.__wordtxt_filename + ' not found. Defered load will also fail')

        self.__wordtxt = None
        self.__len = None
        self.__pos = 0
        self.__next_line = None

    def __load(self):
        print('Loading wordtxt ' + self.__wordtxt_filename + '...')
        self.f = open(self.__wordtxt_filename)
        self.__wordtxt = self.f

    def has_data(self):
        if self.__next_line is not None:
            return True
        if self.__wordtxt is None:
            self.__load()
            try:
                self.__next_line = next(self.__wordtxt)
                return True
            except:
                self.__next_line = None
        return False

    def get(self, count=1):
        if self.__wordtxt is None:
            self.__load()
        if self.__next_line is None:
            self.__next_line = next(self.__wordtxt)
        res = self.__next_line
        try:
            self.__next_line = next(self.__wordtxt)
        except:
            self.__next_line = None

        return res
