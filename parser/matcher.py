#!/usr/bin/env python
# -*- #coding: utf8 -*-


import common.config
import matchcmn


class WordMatcher(object):
    def __init__(self):
        self.match_dict = {}
        self.__load_linkdefs()

    def __load_module(self, path):
        parts = ['parser', 'lang'] + path.split('/')
        root = parts[0]
        parts = parts[1:]
        path = root
        obj = __import__(root, globals(), locals(), root)
        for p in parts:
            path += '.' + p
            obj = __import__(str(path), globals(), locals(), str(path))
        return obj

    def __load_linkdefs(self):
        cfg = common.config.Config()
        for linkdefs_dir in cfg['/parser/linkdefs']:
            obj = self.__load_module(linkdefs_dir)
            for m in obj.load_linkdefs():
                self.add_matcher(m())

    def add_matcher(self, matcher):
        pos1_name, pos2_name = matcher.get_pos_names()
        self.__add_cmp(pos1_name, pos2_name, matcher)

    def __add_cmp(self, p1, p2, matcher):
        if p1 in self.match_dict:
            d = self.match_dict[p1]
        else:
            d = self.match_dict[p1] = {}
        if p2 in d:
            d[p2].append(matcher)
        else:
            d[p2] = [matcher, ]

    def get_matchers(self, pos1_name, pos2_name):
        try:
            return self.match_dict[pos1_name][pos2_name]
        except:
            return []

    def match(self, wf1, wf2):
        for m in self.get_matchers(wf1.get_pos(), wf2.get_pos()):
            return m.match(wf1, wf2)
        return matchcmn.invariantBool()

matcher = None


def load():
    global matcher
    matcher = WordMatcher()


def match(wf1, wf2):
    return matcher.match(wf1, wf2)
