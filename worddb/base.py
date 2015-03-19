#!/usr/bin/env python
# -*- #coding: utf8 -*-


import sqlite3


class Worddb(object):
    def __init__(self, dbfilename, rw=False):
        self.__init_connection(dbfilename)
        self.__load_classes()

    def __load_classes(self):
        self.classes = WordClasses(self.conn, self.cursor)

    def __init_connection(self, dbfilename):
        self.dbfilename = dbfilename
        self.conn = sqlite3.connect(dbfilename)
        self.cursor = self.conn.cursor()

    def get_alphabet(self):
        self.cursor.execute(u'SELECT * FROM alphabet ;')
        return self.cursor.fetchall()

    def check_word(self, word):
        for w in word:
            if w not in self.alphabet:
                return False
        return True

    def __get_word_forms(self, word_id):
        res = []
        self.cursor.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.root=?);', (word_id,))
        for word_id, word, root, class_id in self.cursor.fetchall():
            res.append({"word": word, "class_id": class_id})
        return res

    def get_class_info(self, class_id):
        return self.classes.get_class_by_id(class_id)

    def get_word_info(self, word):
        present_ids = []

        original_word = word

        self.cursor.execute('SELECT word_ids FROM wordlist WHERE (wordlist.word=?);', (word,))
        ids = self.cursor.fetchall()
        res = []
        if len(ids) == 0:
            return None
        ids = eval(ids[0][0])
        for i, in ids:
            if i in present_ids:
                continue
            present_ids.append(i)

            entry = {}
            self.cursor.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.word_id=?);', (i, ))
            word_id, word, root, class_id = self.cursor.fetchall()[0]
            present_ids.append(word_id)
            form = []
            if root == -1:
                # Word is primary
                entry["primary"] = {"word": word, "class_id": class_id}
                entry["forms"] = self.__get_word_forms(word_id)
            else:
                # Word is just form
                self.cursor.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.word_id=?);', (root,))
                word_id, word, root, class_id = self.cursor.fetchall()[0]
                if word_id in present_ids:
                    continue
                present_ids.append(word_id)
                entry["primary"] = {"word": word, "class_id": class_id}
                entry["forms"] = self.__get_word_forms(word_id)

            if entry["primary"]["word"] == original_word:
                class_id = entry["primary"]["class_id"]
                form.append({"word": original_word, "class_id": class_id, "info": self.get_class_info(class_id)})
            for f in entry["forms"]:
                if f["word"] == original_word:
                    class_id = f["class_id"]
                    form.append({"word": original_word, "class_id": class_id, "info": self.get_class_info(class_id)})
            entry["form"] = form
            res.append(entry)
        return res

    def word_info_str(self, info):
        res = "form: ["
        for f in info['form']:
            res += '{'
            for k, v in f.items():
                if isinstance(v, unicode):
                    res += k + ": "
                    res += v
                    res += ', '
                elif isinstance(v, str):
                    res += k + ": " + v + ', '
                else:
                    res += k + u": " + repr(v) + u", "
            res += "} "
        res += "]     "

        res += "primary: {"
        for k, v in info['primary'].items():
            if isinstance(v, unicode):
                res += k + ": "
                res += v
                res += ', '
            elif isinstance(v, str):
                res += k + ": " + v + ', '
            else:
                res += k + u": " + repr(v) + u", "
        res += "}   "

        res += "forms: ["
        for f in info['forms']:
            res += '{'
            for k, v in f.items():
                if isinstance(v, unicode):
                    res += k + ": "
                    res += v
                    res += ', '
                elif isinstance(v, str):
                    res += k + ": " + v + ', '
                else:
                    res += k + u": " + repr(v) + u", "
            res += '}'
        res += "]"

        return res


class WordClasses(object):
    def __init__(self, connection, cursor):
        self.json_to_id = {}
        self.id_to_json = {}
        self.conn = connection
        self.cursor = cursor
        self.__load_classes()

    def __table_exists(self, name):
        self.cursor.execute('SELECT name from sqlite_master WHERE (type==\'table\');')
        tables = self.cursor.fetchall()
        return name in tables

    def __load_classes(self):
        if not self.__table_exists('word_classes'):
            return

        self.cursor.execute('SELECT * from word_classes;')
        for cid, json_info in self.cursor.fetchall():
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
