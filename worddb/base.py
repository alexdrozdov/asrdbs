#!/usr/bin/env python
# -*- #coding: utf8 -*-


import json
import common.db
import common.shadow


class Worddb(common.db.Db):
    def __init__(self, dbfilename, rw=False, no_classes=False):
        common.db.Db.__init__(self, dbfilename=dbfilename, rw=rw)
        if not no_classes:
            self.__load_classes()
        self.__wi_shadow = WordInfoShadow(reuse_db=self)

    def __load_classes(self):
        self.classes = WordClasses(reuse_db=self)

    def get_alphabet(self):
        return self.execute(u'SELECT * FROM alphabet ;').fetchall()

    def check_word(self, word):
        for w in word:
            if w not in self.alphabet:
                return False
        return True

    def get_word_info(self, word):
        return self.__wi_shadow.get(word)

    def get_wordlist_by_word(self, word):
        e = self.execute('SELECT uword_id, word, cnt FROM wordlist WHERE (wordlist.word=?);', (word, )).fetchall()
        if len(e) == 0:
            return None
        u, w, c = e[0]
        return WordlistEntry(u, w, c)

    def get_class_info(self, class_id):
        return self.classes.get_class_by_id(class_id)


class WordClasses(common.db.Db):
    def __init__(self, reuse_db, rw=False):
        common.db.Db.__init__(self, reuse_db=reuse_db, rw=rw)
        self.json_to_id = {}
        self.id_to_json = {}
        self.__load_classes()

    def __table_exists(self, name):
        self.execute('SELECT name from sqlite_master WHERE (type==\'table\');')
        tables = self.fetchall()
        for t, in tables:
            if name == t:
                return True
        return False

    def __load_classes(self):
        if not self.__table_exists(u'word_classes'):
            return

        self.execute('SELECT * from word_classes;')
        for cid, json_info in self.fetchall():
            self.json_to_id[json_info] = cid
            self.id_to_json[cid] = json_info

    def class_exists(self, json_info):
        return self.json_to_info.has_key(json_info)

    def get_class_id(self, json_info):
        if self.json_to_id.has_key(json_info):
            return self.json_to_id[json_info]
        self.add_class(json_info)
        return self.json_to_id[json_info]

    def get_class_by_id(self, cid):
        return self.id_to_json[cid]


class WordlistEntry(object):
    def __init__(self, uword_id, word, count):
        self.__uword_id = uword_id
        self.__word = word
        self.__count = count if count is not None else 0

    def incr(self, val=1):
        self.__count += val

    def get_uword_id(self):
        return self.__uword_id

    def get_word(self):
        return self.__word

    def get_count(self):
        return self.__count


class WordInfoShadow(common.db.Db, common.shadow.Shadow):
    def __init__(self, reuse_db, lru_len=1000):
        common.shadow.Shadow.__init__(self, lru_len=lru_len)
        common.db.Db.__init__(self, reuse_db=reuse_db)

    def get_object_cb(self, objid):
        word = objid
        jblob = self.execute('SELECT blob WHERE (word_blobs.word=?);', (word,)).fetchall()[0]
        return json.loads(jblob)

    def dump_object_cb(self, obj):
        pass
