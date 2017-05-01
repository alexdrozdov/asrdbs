#!/usr/bin/env python
# -*- #coding: utf8 -*-


import re
from common.singleton import singleton
import parser.spare.wordform
from parser.spare.wordform import WordFormFabric


class Tokenizer(object):
    def __init__(self):
        super().__init__()

    @staticmethod
    def tokenize(string):
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


class TokenMapperImpl(object):
    def __init__(self, worddb_file):
        super().__init__()
        self.__wff = WordFormFabric(worddb_file)

    def map(self, tokens):
        return [
            self.__wff.create(word_pos_word[1], word_pos_word[0])
            for word_pos_word in enumerate(tokens)
        ]


@singleton
class TokenMapper(TokenMapperImpl):
    pass


class Parser(object):
    def __init__(object):
        pass


class Sentence(object):
    def __init__(self, forms_array):
        self.__forms = forms_array

    def finalize(self):
        if not isinstance(self.__forms[-1], parser.spare.wordform.SentenceFini):
            self.__forms.append(parser.spare.wordform.SentenceFini())
        return self

    @staticmethod
    def from_string(s):
        tokens = tokenize(s)
        forms = map_tokens(tokens)
        return Sentence(forms)

    @staticmethod
    def from_array(a):
        return Sentence([i for i in a])

    @staticmethod
    def from_sentence(s):
        return Sentence.from_string(s).finalize()

    def __iter__(self):
        return iter(self.__forms)


def tokenize(s):
    return Tokenizer.tokenize(s)


def map_tokens(tokens):
    return TokenMapper().map(tokens)
