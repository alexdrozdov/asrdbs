#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Entry(object):
    def __init__(self):
        pass


class Sentence(object):
    def __init__(self, entries):
        self.__entries = entries


class Paragraph(object):
    def __init__(self, sentences):
        self.__sentences = sentences


class Symbol(object):
    nums = '1234567890'
    alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЗЖИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    syntax = '.,;!?-:'

    def __init__(self, symbol):
        self.__symbol = symbol

    def get(self):
        return self.__symbol

    def is_russian(self):
        return self.is_letter() or self.is_syntax() or self.is_number()

    def is_syntax(self):
        return self.__symbol in Symbol.syntax

    def is_letter(self):
        return self.__symbol in Symbol.alphabet

    def is_number(self):
        return self.__symbol in Symbol.nums


class TextParser(object):
    def __init__(self, txt):
        self.__txt = self.__split(txt)
        self.__pos = 0
        self.__len = len(txt)

    def def_state(self, s):
        if s.is_syntax():
            return self.def_state
        if s.is_letter():
            return self.st_word
        if s.is_number():
            return self.st_num

    def st_word(self, s):
        if s.is_syntax():
            if s.is_hyphen():
                return self.st_possible_wrap
            self.__finalize_word()
            if s.is_sentence_fin():
                self.__finalize_sentence(s)
                return self.def_state
            self.__add_syntax()
            return self.def_state

        if s.is_letter():
            self.__extend_word(s)
            return self.st_word

        if s.is_number():
            self.__extend_word(s)
            return self.st_word

        if s.is_space():
            self.__finalize_word()
            return self.st_space

    def st_space(self, s):
        if s.is_syntax():
            if s.is_hyphen() or s.is_dash():
                return self.st_dash
            if s.is_sentence_fin():
                self.__finalize_sentence()
            return self.def_state
        if s.is_cr():
            self.__cr_seq_len = 1
            return self.st_crlf
        if s.is_lf():
            self.__lf_seq_len = 1
            return self.st_crlf
        if s.is_letter():
            self.__start_word(s)
            return self.st_word
        if s.is_number():
            self.__start_numeric(s)
            return self.st_numeric

    def st_crlf(self, s):
        pass

    def st_dash(self, s):
        if s.is_syntax():
            if s.is_hyphen() or s.is_dash():
                return self.st_dash
            self.__finalize_dash()
            self.__add_syntax(s)
            return self.st_space
        if s.is_letter() or s.is_number():
            return self.def_state
        if s.is_cr() or s.is_lf():
            return self.def_state


    def st_possible_wrap(self, s):
        if s.is_cr():
            if self.__cr_seq_len == 0:
                self.__cr_seq_len += 1
                return self.st_possible_wrap
            return self.def_state
        if s.is_lf():
            if self.__lf_seq_len == 0:
                self.__lf_seq_len += 1
                return self.st_possible_wrap
            return self.def_state
        if s.is_letter():
            self.__extend_word(s)
            return self.st_word
        if s.is_letter():
            return self.def_state

    def __split(self, txt):
        state = self.def_state
        for t in txt:
            s = Symbol(t)
            if not t.is_russian():
                state = state(s)
                continue

    def next(self, count):
        pass

    def has_data(self):
        return self.__pos < self.__len


if __name__ == '__main__':
    pass
