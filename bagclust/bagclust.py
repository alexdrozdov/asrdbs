#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import base


class BagClustdb(base.BaseClustdb):
    def __init__(self, dbfilename):
        base.BagClustdb.__init__(self, dbfilename, rw=False)


def common_startup():
    if os.path.exists("./bagclustdb.db"):
        return BagClustdb('./bagclustdb.db')
    mdb = BagClustdb('./bagclustdb.db')
    return mdb

if __name__ == '__main__':
    mdb = common_startup()
