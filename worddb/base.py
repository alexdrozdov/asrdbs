#!/usr/bin/env python
# -*- #coding: utf8 -*-


import common.db


class Worddb(common.db.Db):
    def __init__(self, dbfilename, rw=False, no_classes=False):
        common.db.Db.__init__(self, dbfilename=dbfilename, rw=rw)
        if not no_classes:
            self.__load_classes()

    def __load_classes(self):
        self.classes = WordClasses(reuse_db=self)

    def get_alphabet(self):
        return self.execute(u'SELECT * FROM alphabet ;').fetchall()

    def check_word(self, word):
        for w in word:
            if w not in self.alphabet:
                return False
        return True

    def __get_word_forms(self, word_id):
        res = []
        self.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.root=?);', (word_id,))
        for word_id, word, root, class_id in self.fetchall():
            res.append({"word": word, "class_id": class_id})
        return res

    def get_wordlist_by_word(self, word):
        e = self.execute('SELECT uword_id, word, cnt FROM wordlist WHERE (wordlist.word=?);', (word, )).fetchall()
        if len(e) == 0:
            return None
        u, w, c = e[0]
        return WordlistEntry(u, w, c)

    def get_class_info(self, class_id):
        return self.classes.get_class_by_id(class_id)

    def get_word_info(self, word):
        present_ids = []

        original_word = word

        ids = self.execute('SELECT word_ids FROM wordlist WHERE (wordlist.word=?);', (word,)).fetchall()
        res = []
        if len(ids) == 0:
            return None
        ids = eval(ids[0][0])
        for i, in ids:
            if i in present_ids:
                continue
            present_ids.append(i)

            entry = {}
            self.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.word_id=?);', (i, ))
            word_id, word, root, class_id = self.fetchall()[0]
            present_ids.append(word_id)
            form = []
            if root == -1:
                # Word is primary
                entry["primary"] = {"word": word, "class_id": class_id}
                entry["forms"] = self.__get_word_forms(word_id)
            else:
                # Word is just form
                self.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.word_id=?);', (root,))
                word_id, word, root, class_id = self.fetchall()[0]
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
        res = "["
        for wi in info:
            res += self.__word_form_info_str(wi)
            res += ', '
        res += ']'
        return res

    def __word_form_info_str(self, info):
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
