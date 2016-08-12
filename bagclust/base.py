#!/usr/bin/env python
# -*- #coding: utf8 -*-


import json
import common.db
import common.shadow


class BagClustdb(common.db.Db):
    def __init__(self, dbfilename, rw=False):
        common.db.Db.__init__(self, dbfilename=dbfilename, rw=rw)
        self.__b_shadow = BlobShadow(reuse_db=self)

    def flush_bags(self):
        self.__b_shadow.flush()

    def get_bag(self, word):
        return self.__b_shadow.get_object(word)


class WordNeighbor(object):
    def __init__(self, word, info):
        self.__word = word
        self.__info = info

    def add_instance(self, distance=None):
        if distance is None:
            self.__info['cnt'] += 1
            return
        d_sum = self.__info['avg_dist'] * self.__info['cnt']
        d_sum += float(distance)
        self.__info['cnt'] += 1
        self.__info['avg_dist'] = d_sum / self.__info['cnt']


class BagEntry(object):
    def __init__(self, blob_id, word, info):
        self.__blob_id = blob_id
        self.__word = word
        self.__info = info
        if 'neighbors' not in self.__info:
            self.__info['neighbors'] = {}

    def get_blob_id(self):
        return self.__blob_id

    def get_word(self):
        return self.__word

    def get_info(self):
        return self.__info

    def get_jblob(self):
        return json.dumps(self.__info, ensure_ascii=False)

    def get_neighbor(self, word):
        neighbors = self.__info['neighbors']
        if word not in neighbors:
            neighbors[word] = {'cnt': 0, 'avg_dist': 0.0}
        return WordNeighbor(word, neighbors[word])

    def add_neighbor(self, word, distance=None):
        ne = self.get_neighbor(word)
        ne.add_instance(distance)


class BlobShadow(common.db.Db, common.shadow.Shadow):
    def __init__(self, reuse_db, lru_len=100000):
        common.shadow.Shadow.__init__(self, lru_len=lru_len)
        common.db.Db.__init__(self, reuse_db=reuse_db)

    def get_object_cb(self, objid):
        word = objid
        jblob = self.execute('SELECT blob_id, word, blob FROM blobs WHERE (blobs.word=?);', (word,)).fetchall()
        if len(jblob) > 0 and len(jblob[0]) > 0:
            blob_id, word, jblob = jblob[0]
            return BagEntry(blob_id, word, json.loads(jblob))
        return BagEntry(None, objid, {})

    def dump_object_cb(self, obj):
        if obj is None:
            return
        bag_entry = obj
        blob_id = bag_entry.get_blob_id()
        if blob_id is None:
            self.execute('INSERT OR IGNORE INTO blobs (word, blob) VALUES (?,?)', (bag_entry.get_word(), bag_entry.get_jblob()))
        else:
            self.execute('UPDATE blobs SET blob=? WHERE (blobs.blob_id=?);', (bag_entry.get_jblob(), blob_id))
