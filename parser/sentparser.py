#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import re
from parser.wordform import WordFormFabric


class Link(object):
    def __init__(self, rule, master, slave, uniq=None):
        self.__rule = rule
        if uniq is None:
            self.__uniq = str(uuid.uuid1())
        else:
            self.__uniq = uniq
        self.__master = master
        self.__slave = slave

    def get_uniq(self):
        return self.__uniq

    def get_rule(self):
        return self.__rule

    def get_master(self):
        return self.__master

    def get_slave(self):
        return self.__slave

    def set_ms(self, master, slave):
        self.__master = master
        self.__slave = slave


class Tokenizer(object):
    def __init__(self):
        pass

    def tokenize(self, string):
        if isinstance(string, list):
            return string
        return filter(
            lambda s:
                s,
            re.sub(
                r'\.\s*$',
                r' . ',
                re.sub(
                    r"(,\s)",
                    r' \1',
                    re.sub(
                        r"([^\w\.\-\/,])",
                        r' \1 ',
                        string,
                        flags=re.U
                    ),
                    flags=re.U
                ),
                flags=re.U
            ).split()
        )


class TokenMapper(object):
    def __init__(self, worddb_file):
        self.__wff = WordFormFabric(worddb_file)

    def map(self, tokens):
        return map(
            lambda (word_pos, word): self.__wff.create(word, word_pos),
            enumerate(tokens)
        )
