#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sys
import argparse
import os
import adaptors.wordtxt
import adaptors.libdb
import bagclust.builders
import worddb.worddb


def parse_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--create', action='store_true', default=False)
    parser.add_argument('-i', '--libdb')
    parser.add_argument('-w', '--worddb')
    parser.add_argument('-l', '--limit', type=int, default=0)
    parser.add_argument('db')
    res = parser.parse_args(sys.argv[1:])

    if not res.create:
        raise ValueError('--create option not specified')

    if res.libdb is None or res.worddb is None:
        raise ValueError('--create option requires --libdb and --worddb options')

    if res.limit == 0:
        res.limit = None

    return res


def execute(opts):
    bcdb = bagclust.builders.BagClustdbBuilder(opts.db, rw=True)
    if opts.create:
        if not os.path.exists(opts.worddb):
            raise ValueError('File ' + opts.worddb + ' not found')
        if not os.path.exists(opts.libdb):
            raise ValueError('File ' + opts.libdb + ' not found')
        ldb = adaptors.libdb.LibrudbWordsAdapter(opts.libdb)
        wddb = worddb.worddb.Worddb(opts.worddb)
        bcdb.add_words(ldb, wddb, window_width=8, max_count=opts.limit)

if __name__ == '__main__':
    opts = parse_opts()
    execute(opts)
