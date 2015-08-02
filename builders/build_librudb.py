#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sys
import argparse
import os
import adaptors.libdir
import librudb.builders


def parse_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--append')
    parser.add_argument('-l', '--limit', type=int, default=0)
    parser.add_argument('db')
    res = parser.parse_args(sys.argv[1:])

    if not res.append:
        raise ValueError('--append option with list file name required')

    if res.limit == 0:
        res.limit = None

    return res


def execute(opts):
    lrdb = librudb.builders.LibrudbBuilder(opts.db, rw=True)
    if opts.append:
        if not os.path.exists(opts.append):
            raise ValueError('File ' + opts.append + ' not found')
        lrdir = adaptors.libdir.LibdirAdapter(opts.append)
        lrdb.add_files(lrdir, max_count=opts.limit)


if __name__ == '__main__':
    opts = parse_opts()
    execute(opts)
