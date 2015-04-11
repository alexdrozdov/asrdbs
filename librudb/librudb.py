#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import base


class DbRoIterator(object):
    def __init__(self, db, table, coloumns, conditions=None, chunk_size=10):
        self.__db = db
        self.__offset = 0
        self.__prefetched_offset = 0
        self.__prefetched_len = 0
        self.__chunk_size = chunk_size
        self.__conditions = conditions
        self.__query_pattern = 'SELECT ' + ', '.join(coloumns) + ' FROM ' + table
        if conditions is not None:
            self.__query_pattern += ' WHERE (' + '=? AND '.join([c[0] for c in conditions])
            self.__query_pattern += '=?)'
        self.__query_pattern += ' OFFSET ? LIMIT ?;'

        self.__prefetched = None

    def __prefetch(self):
        if self.__conditions is not None:
            qlist = [c[1] for c in self.__conditions]
        else:
            qlist = []
        qlist.extend([self.__offset, self.__chunk_size])
        qtuple = tuple(qlist)
        self.__prefetched = self.__db.cursor.execute(self.__query_pattern, qtuple).fetchall()
        self.__prefetched_len = len(self.__prefetched)
        self.__offset += self.__prefetched_len
        self.__prefetched_offset = 0

    def has_data(self):
        if self.__prefetched is None or self.__prefetched_len <= self.__prefetched_offset:
            self.__prefetch()
        return self.__prefetched_offset < self.__prefetched_len

    def get(self, entry_count=1):
        if self.__prefetched is None:
            self.__prefetch()
        res = []
        for i in range(entry_count):
            if self.__prefetched_len <= self.__prefetched_offset:
                self.__prefetch()
            if self.__prefetched_len <= self.__prefetched_offset:
                return res
            res.append(self.__prefetched[self.__prefetched_offset])
            self.__prefetched_offset += 1


class Librudb(base.Librudb):
    def __init__(self, dbfilename):
        base.Librudb.__init__(self, dbfilename, rw=False)


def common_startup():
    if os.path.exists("./librudb.db"):
        return Librudb('./librudb.db')
    lrdb = Librudb('./librudb.db')
    return lrdb

if __name__ == '__main__':
    lrdb = common_startup()
