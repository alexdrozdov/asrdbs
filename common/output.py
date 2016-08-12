#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import time


class OutputPath(object):
    def __init__(self, def_path=None):
        self.__pathes = {}
        self.__defpath = def_path if def_path is not None else './output'
        self.__defpath = os.path.join(self.__defpath, time.asctime().replace(' ', '_').replace(':', '-'))

    def get_output_dir(self, subpath):
        if subpath in self.__pathes:
            return self.__pathes[subpath]
        path = os.path.join(self.__defpath, subpath)
        if not os.path.exists(path):
            os.makedirs(path)
        elif not os.path.isdir(path):
            raise OSError('Path {0} is file')
        self.__pathes[subpath] = path
        return path

    def get_output_file(self, subpath, filename):
        if isinstance(subpath, list):
            subpath = [e for e in subpath if e is not None]
            subpath = os.path.join(*subpath)
        path = self.get_output_dir(subpath)
        return os.path.join(path, filename)


try:
    type(output)
except:
    output = OutputPath()
