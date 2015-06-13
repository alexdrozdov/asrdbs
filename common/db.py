#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import sqlite3


class Db(object):
    def __init__(self, dbfilename=None, reuse_db=None, rw=False):
        if dbfilename is not None:
            self.__dbfilename = dbfilename
            self.__rw = rw
            self.__init_connection()
        elif reuse_db is not None:
            if rw and not reuse_db.__rw:
                raise ValueError('Tried to reuse db opened with ro as rw')
            self.__rw = reuse_db.__rw
            self.__dbfilename = reuse_db.__dbfilename
            self.__reuse_connection(reuse_db)
        else:
            raise ValueError('Neither dbfilename nor reuse_db specified')

    def __init_connection(self):
        if not self.__rw:
            fd = os.open(self.__dbfilename, os.O_RDONLY)
            self.__conn = sqlite3.connect('/dev/fd/{0}'.format(fd))
            os.close(fd)
        else:
            self.__conn = sqlite3.connect(self.__dbfilename)
        self.__cursor = self.__conn.cursor()

    def __reuse_connection(self, reuse_db):
        self.__conn = reuse_db.__conn
        self.__cursor = self.__conn.cursor()

    def commit(self):
        self.__conn.commit()

    def execute(self, query, params=()):
        return self.__cursor.execute(query, params)

    def executemany(self, query, params=[()]):
        return self.__cursor.executemany(query, params)

    def mksync(self):
        self.__cursor.execute('PRAGMA synchronous=0;')

    def fetchone(self):
        return self.__cursor.fetchone()

    def fetchall(self):
        return self.__cursor.fetchall()

    def get_lastrowid(self):
        return self.__cursor.lastrowid


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
        self.__query_pattern += ' LIMIT ? OFFSET ?;'

        self.__prefetched = None

    def __prefetch(self):
        if self.__conditions is not None:
            qlist = [c[1] for c in self.__conditions]
        else:
            qlist = []
        qlist.extend([self.__chunk_size, self.__offset])
        qtuple = tuple(qlist)
        self.__prefetched = self.__db.execute(self.__query_pattern, qtuple).fetchall()
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
        return res
