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
