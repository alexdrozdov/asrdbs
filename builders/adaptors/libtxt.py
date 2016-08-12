#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os


class LibtxtAdapter(object):
    def __init__(self, libtxt_filename):
        self.__libtxt_filename = libtxt_filename

        if not os.path.exists(self.__libtxt_filename):
            raise IOError('File ' + self.__libtxt_filename + ' not found. Defered load will also fail')

        self.__words = None
        self.__len = None
        self.__pos = 0

    def __load(self):
        print('Loading libtxt ' + self.__libtxt_filename + '...')
        with open(self.__libtxt_filename) as f:
            txt = f.read().decode('utf8')

        unwanted_chars = '*+-()@#№%^&_{}[]"\'/\\<>~=,.:;!?\r\n'
        tt = {ord(c): ord(' ') for c in unwanted_chars}
        self.__words = txt.translate(tt).strip().split()
        self.__len = len(self.__words)

    def has_data(self):
        if self.__words is None:
            self.__load()
        return self.__pos < self.__len

    def get(self, count=1):
        if self.__words is None:
            self.__load()
        res = self.__words[self.__pos:self.__pos+count]
        self.__pos += len(res)
        return res
