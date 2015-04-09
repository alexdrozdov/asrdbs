#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import base


class Librudb(base.Librudb):
    def __init__(self, dbfilename):
        base.Librudb.__init__(self, dbfilename, rw=False)


def common_startup():
    if os.path.exists("./librudb.db"):
        return Worddb('./librudb.db')
    lrdb = Worddb('./librudb.db')
    return lrdb

if __name__ == '__main__':
    lrdb = common_startup()
