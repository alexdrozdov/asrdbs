#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sys
import argparse
import os
import adaptors.wordtxt
import worddb.builders


def parse_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--create', action='store_true', default=False)
    parser.add_argument('-o', '--optimize', action='store_true', default=False)
    parser.add_argument('-t', '--txt')
    parser.add_argument('db')
    res = parser.parse_args(sys.argv[1:])

    if not res.create and not res.optimize:
        raise ValueError('Neither --create or --optimize option specified')

    if res.create and res.txt is None:
        raise ValueError('--create option requires --txt option specified to source file')

    return res


def execute(opts):
    wddb = worddb.builders.WorddbBuilder(opts.db, rw=True)
    if opts.create:
        if not os.path.exists(opts.txt):
            raise ValueError('File ' + opts.txt + ' not found')
        wdtxt = adaptors.wordtxt.WordtxtAdapter(opts.txt)
        wddb.add_alphabet(u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
        wddb.add_words(wdtxt)
    if opts.optimize:
        wddb.build_optimized()


if __name__ == '__main__':
    opts = parse_opts()
    execute(opts)
