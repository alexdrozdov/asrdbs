#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os


class LibdirAdapter(object):
    def __init__(self, listfile):
        self.__listfile = listfile

        if not os.path.exists(self.__listfile):
            raise IOError('File ' + self.__listfile + ' not found. Defered load will also fail')

        self.__file_list = None
        self.__len = None
        self.__pos = 0

    def __load(self):
        print('Loading dir list file ' + self.__listfile + '...')
        with open(self.__listfile) as f:
            self.__file_list = f.readlines()
        self.__len = len(self.__file_list)
        self.__pos = 1

    def has_data(self):
        if self.__file_list is None:
            self.__load()
        return self.__pos < self.__len

    def get(self, count=1):
        if not self.has_data():
            return None
        res = self.__file_list[self.__pos].splitlines()[0]
        self.__pos += 1
        return res
