#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from . import base


class Worddb(base.Worddb):
    def __init__(self, dbfilename):
        base.Worddb.__init__(self, dbfilename, rw=False)


def common_startup():
    if os.path.exists("./worddb.db"):
        return Worddb('./worddb.db')
    mdb = Worddb('./worddb.db')
    return mdb

if __name__ == '__main__':
    mdb = common_startup()
