#!/usr/bin/env python
# -*- #coding: utf8 -*-


import re
from parser.wordform import WordFormFabric


class Tokenizer(object):
    def __init__(self):
        pass

    def tokenize(self, string):
        if isinstance(string, list):
            return string
        return [s for s in re.sub(
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
            ).split() if s]


class TokenMapper(object):
    def __init__(self, worddb_file):
        self.__wff = WordFormFabric(worddb_file)

    def map(self, tokens):
        return [self.__wff.create(word_pos_word[1], word_pos_word[0]) for word_pos_word in enumerate(tokens)]


class Parser(object):
    def __init__(object):
        pass
