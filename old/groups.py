#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import sqlite3


class Forms:
    terms = {
        "parts_of_speech": {
            "noun": u"сущ",
            "adjective": u"прл",
            "verb": u"гл",
            "participal": [u"прч", u"дееп"],
            "union": [u"союз", u"межд", u"предик"],
            "particle": u"част",
            "numeral": u"числ",
            "pronoun": u"мест",
            "adverb": u"нар",
            "preposition": u"предл",
        },

        "count": {
            "singilar": u"ед",
            "plural": u"мн"
        },

        "gender": {
            "male": u"муж",
            "female": u"жен",
            "neuter": u"ср"
        },

        "animation": {
            "animated": u"одуш",
            "inanimated": u"неод"
        },

        "case": {
            "nominative": u"им",
            "genitive": u"род",
            "dative": u"дат",
            "accusative": u"вин",
            "ablative": u"тв",
            "prepositional": u"пр"
        },

        "verb_form": {
            "perfect": u"несов",
            "imperfect": u"сов"
        },

        "time": {
            "infinitive": u"инф",
            "past": u"прош",
            "present": u"наст",
            "future": u"буд"
        }
    }

    def __init__(self):
        self.transforms = {}
        self.unknown = {}
        for term_name, term_values in Forms.terms.items():
            for term_value, term_code in term_values.items():
                if isinstance(term_code, list):
                    for c in term_code:
                        self.transforms[c] = {"term": term_name, "value": term_value, "code": c}
                else:
                    self.transforms[term_code] = {"term": term_name, "value": term_value, "code": term_code}

    def generate_classes(self):
        pass

    def list_to_terms(self, l):
        res = {}
        for i in l:
            i = i.decode("utf8")
            try:
                term = self.transforms[i]
                res[term["term"]] = term["value"]
            except:
                if self.unknown.has_key(i):
                    self.unknown[i] += 1
                else:
                    self.unknown[i] = 1
        return res

    def print_unknowns(self):
        for k, v in self.unknown.items():
            print k.encode("utf8"), v


class MorfWordGroup(object):
    def __init__(self):
        self.primary = None
        self.forms = []

    def add_entry(self, word, info):
        if None == self.primary:
            self.primary = (word, info)
            return
        self.forms.append((word, info))

    def len(self):
        if None == self.primary:
            return 0
        return 1+len(self.forms)


class WordClasses(object):
    def __init__(self, connection, cursor):
        self.json_to_id = {}
        self.id_to_json = {}
        self.conn = connection
        self.cursor = cursor
        self.__create_tables()
        self.__load_classes()

    def __create_tables(self):
        commands = [
        'CREATE TABLE IF NOT EXISTS word_classes (class_id INTEGER PRIMARY KEY, json_info TEXT, UNIQUE(json_info));',
]
        for c in commands:
            self.cursor.execute(c)
        self.conn.commit()

    def __load_classes(self):
        self.cursor.execute('SELECT * from word_classes;')
        for cid, json_info in self.cursor.fetchall():
            self.json_to_id[json_info] = cid
            self.id_to_json[cid] = json_info

    def add_class(self, json_info):
        self.cursor.execute('INSERT INTO word_classes (json_info) VALUES (?);', (json_info,))
        cid = self.cursor.lastrowid
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




def load_db(max_words=None):
    if os.path.exists("./morfdb.db"):
        return Morfdb("morfdb.db")
    else:
        mdb = Morfdb("morfdb.db")
        mdb.add_alphabet(u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
        mdb.load_words("morh.txt", max_words=max_words)
        return mdb

db = load_db()

if __name__ == '__main__':
    db.build_wordlist()
