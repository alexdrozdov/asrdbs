#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sys
import argparse
import os
import adaptors.wordb
import graphdb.builders


def parse_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--create', action='store_true', default=False)
    parser.add_argument('-r', '--hardlinks', action='store_true', default=False)
    parser.add_argument('-s', '--softlinks', action='store_true', default=False)
    parser.add_argument('-o', '--optimize', action='store_true', default=False)
    parser.add_argument('-i', '--worddb')
    parser.add_argument('-l', '--limit', type=int, default=0)
    parser.add_argument('db')
    res = parser.parse_args(sys.argv[1:])

    if not res.create and not res.optimize and not res.hardlinks and not res.softlinks:
        raise ValueError('Neither --create or --hardlinks or --softlinks nor --optimize option specified')

    if res.create and res.worddb is None:
        raise ValueError('--create option requires --worddb option specified to source file')

    if res.limit == 0:
        res.limit = None

    if res.create and os.path.exists(res.db):
        raise ValueError('--create option suggested while ' + res.db + ' already exists. Remove file first')

    return res


def execute(opts):
    gdb = graphdb.builders.GraphdbBuilder(opts.db, rw=True)
    if opts.create:
        if not os.path.exists(opts.worddb):
            raise ValueError('File ' + opts.worddb + ' not found')
        wddb = adaptors.wordb.WorddbBlobsAdapter(opts.worddb)
        gdb.add_alphabet(u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
        gdb.add_words(wddb, max_count=opts.limit)
    if opts.hardlinks:
        gdb.generate_hardlinks(max_count=opts.limit)
    if opts.softlinks:
        gdb.generate_softlinks(max_count=opts.limit)
    if opts.optimize:
        gdb.generate_optimized(max_count=opts.limit)


if __name__ == '__main__':
    opts = parse_opts()
    execute(opts)
