#!/usr/bin/env python
# -*- #coding: utf8 -*-


import base


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


class Worddb(base.Worddb):
    def __init__(self, dbfilename):
        base.Worddb.__init__(self, dbfilename)
        self.__create_tables()

    def __load_classes(self):
        self.classes = WordClassesBuilder(self.conn, self.cursor)

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS words (word_id INTEGER PRIMARY KEY, word TEXT, root INTEGER, commit_id INTEGER, class_id INTEGER, UNIQUE(word,class_id) );',
                    'CREATE TABLE IF NOT EXISTS commits (commit_id INTEGER PRIMARY KEY, commit_time TEXT, comment TEXT);',
                    'CREATE TABLE IF NOT EXISTS alphabet (letter_id INTEGER PRIMARY KEY, letter TEXT, UNIQUE (letter));',
                    'CREATE TABLE IF NOT EXISTS wordlist (uword_id INTEGER PRIMARY KEY, word TEXT, word_ids TEXT, UNIQUE(word));',
                    ]

        for c in commands:
            self.cursor.execute(c)
        self.conn.commit()

    def line_to_form(self, line):
        line_terms = line.split('\t')
        word = line_terms[0]
        line_terms = line_terms[1].split(' ')
        info = self.ft.list_to_terms(line_terms)

        return (word.decode("utf8"), info)

    def add_alphabet(self, alphabet):
        alphabet_tuple = [(a,) for a in alphabet]
        self.cursor.executemany('INSERT OR IGNORE INTO alphabet (letter) VALUES (?);', alphabet_tuple)
        self.conn.commit()

    def add_word_group(self, word_group, commit_string="Automatic commit name"):
        self.cursor.execute('INSERT INTO commits (commit_time, comment)  VALUES (CURRENT_TIMESTAMP, "'+commit_string+'");')
        commit_id = self.cursor.lastrowid

        cid = self.classes.get_class_id(repr(word_group.primary[1]))
        self.cursor.execute('INSERT OR IGNORE INTO words (word, root, commit_id, class_id) VALUES (?,?,?,?)',
                            (word_group.primary[0], -1, commit_id, cid))

        word_id = self.cursor.lastrowid

        words_tuple = [(w, word_id, commit_id, self.classes.get_class_id(repr(i))) for w, i in word_group.forms]
        self.cursor.executemany('INSERT OR IGNORE INTO words (word, root, commit_id, class_id) VALUES (?,?,?,?);', words_tuple)
        self.conn.commit()

    def __build_word_index(self):
        print "Building words index..."
        self.cursor.execute('CREATE INDEX IF NOT EXISTS words_idx ON words (word) ;')
        self.conn.commit()

    def __drop_word_index(self):
        print "Dropping words index..."
        self.cursor.execute('DROP INDEX IF EXISTS words_idx;')

    def __build_wordlist_index(self):
        print "Building wordlist index..."
        self.cursor.execute('CREATE INDEX IF NOT EXISTS wordslist_idx ON wordlist (word) ;')
        self.conn.commit()

    def __recreate_wordlist(self):
        print "Dropping wordlist index..."
        self.cursor.execute('DROP INDEX IF EXISTS wordlist_idx;')
        self.cursor.execute('DROP TABLE IF EXISTS wordlist;')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS wordlist (uword_id INTEGER PRIMARY KEY, word TEXT, word_ids TEXT, UNIQUE(word));')

    def build_wordlist(self):
        print "Building full word list..."
        self.__recreate_wordlist()

        print "Selecting complete word list..."
        query = 'SELECT DISTINCT word FROM words;'
        self.cursor.execute(query)
        words = self.cursor.fetchall()

        word_count = len(words)
        print_step = word_count / 20
        word_cnt = 0
        for w in words:
            self.cursor.execute('SELECT word_id FROM words WHERE (words.word=?)', w)
            word_ids = self.cursor.fetchall()
            self.cursor.execute('INSERT OR IGNORE INTO wordlist (word, word_ids) VALUES (?,?)', (w[0], repr(word_ids)))

            word_cnt += 1
            if word_cnt % print_step == 0:
                print "Ready", word_cnt*100/word_count, "%"

        self.__build_wordlist_index()

    def load_words(self, file_name, max_words=None):
        self.alphabet = [l for n, l in self.get_alphabet()]

        self.__drop_word_index()

        with open(file_name) as f:
            self.cursor.execute('PRAGMA synchronous=0;')

            self.ft = Forms()
            cnt = 0

            wf = MorfWordGroup()
            for line in f.xreadlines():
                if len(line) <= 6:
                    if wf.len() == 0:
                        continue
                    self.add_word_group(wf)
                    wf = MorfWordGroup()
                    if cnt % 1000 == 0:
                        print "Inserted", cnt, "lines"
                    continue

                w, i = self.line_to_form(line)
                w = w.strip()
                if not self.check_word(w):
                    # print "Dropping <"+w+"> with wrong symbols"
                    continue

                wf.add_entry(w, i)

                if max_words is not None and cnt >= max_words:
                    break
                cnt += 1
            self.__build_word_index()

    def __get_word_forms(self, word_id):
        res = []
        self.cursor.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.root=?);', (word_id,))
        for word_id, word, root, class_id in self.cursor.fetchall():
            res.append({"word": word, "class_id": class_id})
        return res


class WordClassesBuilder(base.WordClasses):
    def __init__(self, connection, cursor):
        base.WordClasses.__init__(self, connection, cursor)
        self.__create_tables()

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS word_classes (class_id INTEGER PRIMARY KEY, json_info TEXT, UNIQUE(json_info));', ]
        for c in commands:
            self.cursor.execute(c)
        self.conn.commit()

    def add_class(self, json_info):
        self.cursor.execute('INSERT INTO word_classes (json_info) VALUES (?);', (json_info,))
        cid = self.cursor.lastrowid
        self.json_to_id[json_info] = cid
        self.id_to_json[cid] = json_info

    def get_class_id(self, json_info):
        if self.json_to_id.has_key(json_info):
            return self.json_to_id[json_info]
        self.add_class(json_info)
        return self.json_to_id[json_info]

    def get_class_by_id(self, cid):
        return self.id_to_json[cid]
