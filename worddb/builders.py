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


class WorddbBuilder(base.Worddb):
    def __init__(self, dbfilename, rw=False):
        base.Worddb.__init__(self, dbfilename, no_classes=True)
        self.__create_tables()
        self.__load_classes()
        self.ft = Forms()

    def __load_classes(self):
        self.classes = WordClassesBuilder(self.conn, self.cursor)

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS words (word_id INTEGER PRIMARY KEY, word TEXT, root INTEGER, commit_id INTEGER, class_id INTEGER, UNIQUE(word,class_id) );',
                    'CREATE TABLE IF NOT EXISTS commits (commit_id INTEGER PRIMARY KEY, commit_time TEXT, comment TEXT);',
                    'CREATE TABLE IF NOT EXISTS alphabet (letter_id INTEGER PRIMARY KEY, letter TEXT, UNIQUE (letter));',
                    'CREATE TABLE IF NOT EXISTS wordlist (uword_id INTEGER PRIMARY KEY, word TEXT, word_ids TEXT, count INTEGER, UNIQUE(word));',
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
        self.cursor.execute('CREATE INDEX IF NOT EXISTS words_root_idx ON words (root) ;')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS words_class_idx ON words (class_id) ;')
        self.conn.commit()

    def __drop_word_index(self):
        print "Dropping words index..."
        self.cursor.execute('DROP INDEX IF EXISTS words_idx;')
        self.cursor.execute('DROP INDEX IF EXISTS words_root_idx;')
        self.cursor.execute('DROP INDEX IF EXISTS words_class_idx;')

    def __build_wordlist_index(self):
        print "Building wordlist index..."
        self.cursor.execute('CREATE INDEX IF NOT EXISTS wordslist_idx ON wordlist (word) ;')
        self.conn.commit()

    def __recreate_wordlist(self):
        print "Dropping wordlist index..."
        self.cursor.execute('DROP INDEX IF EXISTS wordlist_idx;')
        self.cursor.execute('DROP TABLE IF EXISTS wordlist;')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS wordlist (uword_id INTEGER PRIMARY KEY, word TEXT, word_ids TEXT, UNIQUE(word));')

    def build_wordlist(self, max_count=None):
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

    def add_words(self, words_iter, max_count=None):
        count = 0
        self.alphabet = [l for n, l in self.get_alphabet()]
        self.__drop_word_index()
        self.cursor.execute('PRAGMA synchronous=0;')

        wf = MorfWordGroup()
        while words_iter.has_data() and (max_count is None or count < max_count):
            line = words_iter.get()
            if len(line) <= 6:
                if wf.len() == 0:
                    continue
                self.add_word_group(wf)
                wf = MorfWordGroup()
                if count % 1000 == 0:
                    print "Inserted", count, "lines"
                continue

            w, i = self.line_to_form(line)
            w = w.strip()
            if not self.check_word(w):
                continue

            wf.add_entry(w, i)

            if max_count is not None and count >= max_count:
                break
            count += 1
        self.__build_word_index()

    def __get_word_forms(self, word_id):
        res = []
        self.cursor.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.root=?);', (word_id,))
        for word_id, word, root, class_id in self.cursor.fetchall():
            res.append({"word": word, "class_id": class_id})
        return res

    def build_optimized(self, max_count=None):
        odb = OptimizedDbBuilder(self)
        odb.build(max_count)

    def count_words(self, word_iter, max_count=None):
        wdc = WorddbCounter(self)
        wdc.add_words(word_iter, max_count)

    def update_wordlist(self, wle):
        if wle is None:
            return
        self.cursor.execute('UPDATE wordlist SET word=? count=? WHERE (wordlist.uword_id=?);', (wle.get_word(), wle.get_count(), wle.get_uword_id()))


class OptimizedDbBuilder(object):
    def __init__(self, dbbuilder):
        self.__dbbuild = dbbuilder

    def __insert_blob(self, word, word_id, blob):
        self.__dbbuild.cursor.execute('INSERT INTO word_blobs (word, word_id, blob) VALUES (?, ?, ?)', (word, word_id, blob))

    def __drop_optimized_table(self):
        print "Dropping existing optimized tables..."
        self.__dbbuild.cursor.execute('DROP INDEX IF EXISTS word_blobs_bw_idx;')
        self.__dbbuild.cursor.execute('DROP INDEX IF EXISTS word_blobs_bi_idx;')
        self.__dbbuild.cursor.execute('DROP TABLE IF EXISTS word_blobs;')
        self.__dbbuild.conn.commit()

        print "Running vacuum..."
        self.__dbbuild.cursor.execute('VACUUM;')
        self.__dbbuild.conn.commit()

    def __create_optimized_table(self):
        print "Creating new optimized tables..."
        self.__dbbuild.cursor.execute('CREATE TABLE IF NOT EXISTS word_blobs (word TEXT, word_id INTEGER, blob TEXT);')
        self.__dbbuild.conn.commit()

    def __disable_synchronous_mode(self):
        print "Disabling synchronous mode..."
        self.__dbbuild.cursor.execute('PRAGMA synchronous=0;')

    def __build_index(self):
        print "Creating index on words..."
        self.__dbbuild.cursor.execute('CREATE INDEX IF NOT EXISTS word_blobs_bw_idx ON word_blobs (word) ;')
        print "Creating index on word ids..."
        self.__dbbuild.cursor.execute('CREATE INDEX IF NOT EXISTS word_blobs_bi_idx ON word_blobs (word_id) ;')
        self.__dbbuild.conn.commit()

    def __build_blobs(self, max_count=None, chunk_size=10000):
        print "Building word blobs..."
        offset = 0
        while True:
            self.__dbbuild.cursor.execute('SELECT word, uword_id FROM wordlist LIMIT ? OFFSET ?;', (chunk_size, offset))
            word_word_ids = self.__dbbuild.cursor.fetchall()
            res_len = len(word_word_ids)
            offset += res_len

            for word, uword_id in word_word_ids:
                info = self.__dbbuild.get_word_info(word)
                blob = self.__dbbuild.word_info_str(info)
                self.__insert_blob(word, uword_id, blob)
            self.__dbbuild.conn.commit()

            print offset, " entries complete"
            if res_len < chunk_size or (max_count is not None and max_count <= offset):
                break

    def build(self, max_count=None):
        print "Started to build optimized table"
        self.__drop_optimized_table()
        self.__create_optimized_table()
        self.__disable_synchronous_mode()
        self.__build_blobs(max_count)
        self.__build_index()
        self.__dbbuild.conn.commit()


class LruEntry(object):
    def __init__(self, obj, left=None, right=None):
        self.__obj = obj
        self.__left = left
        self.__right = right

    def self_extract(self):
        if self.__left is not None:
            self.__left.__right = self.__right
        if self.__right is not None:
            self.__right.__left = self.__left
        self.__left = None
        self.__right = None

    def self_insert_righter_than(self, left_entry):
        self.__left = left_entry
        if left_entry.__right is not None:
            self.__right = left_entry.__right
            self.__right.__left = self
        left_entry.__right = self

    def get_object(self):
        return self.__obj


class Shadow(object):
    def __init_(self, lru_len=1000):
        self.__lru_max_len = lru_len
        self.__cache = {}
        self.__lru_head = None
        self.__lru_tail = None
        self.__lru_len = 0
        self.__obj2objid_dict = {}

    def __pop_tail(self):
        if self.__lru_tail is None or self.__lru_len == 0:
            return
        rm = self.__lru_tail
        self.__lru_tail = self.__lru_tail.__right
        rm.self_extract()
        if self.__lru_tail is None:
            self.__lru_head = None
        self.__lru_len -= 1
        return rm

    def __pop_head(self):
        if self.__lru_head is None or self.__lru_len == 0:
            return
        rm = self.__lru_head
        self.__lru_head = self.__lru_head.__head
        rm.self_extract()
        if self.__lru_head is None:
            self.__lru_tail = None
        self.__lru_len -= 1

    def __del_from_cache(self, lru_entry):
        _, objid = self.__obj2objid_dict.pop(lru_entry)
        _, _ = self.__cache.popitem(objid)

    def __extract_lru(self, lru_entry):
        self.__del_from_cache(lru_entry)
        if self.__lru_tail == lru_entry:
            self.__pop_tail()
            return
        if self.__lru_head == lru_entry:
            self.__pop_head()
            return
        lru_entry.self_extract()
        self.__lru_len -= 1

    def __push_head(self, lru_entry):
        if self.__lru_len >= self.__lru_max_len:
            rm = self.__pop_tail()
            self.dump_object_cb(rm.get_object())
            self.__del_from_cache(rm)
        if self.__lru_head is None:
            self.__lru_head = lru_entry
            self.__lru_tail = lru_entry
        else:
            lru_entry.self_insert_righter_than(self.__lru_head)
            self.__lru_head = lru_entry
        self.__lru_len += 1

    def flush(self):
        pass

    def get_object(self, objid, cache_none=True):
        obj = self.get_object_cb(objid)
        if not cache_none:
            return obj
        if self.__cache.has_key(objid):
            lru = self.__cache[objid]
            if lru != self.__lru_head:
                self.__extract_lru(lru)
                self.__push_head(lru)
            return lru.get_object()
        lru = LruEntry(obj)
        self.__push_head(lru)
        self.__cache[objid] = lru
        self.__obj2objid_dict[lru] = objid
        return lru.get_object()


class WorddbCounter(Shadow):
    def __init__(self, worddb):
        Shadow.__init__(self, lru_len=1000)
        self.__worddb = worddb

    def get_object_cb(self, objid):
        return self.__worddb.get_wordlist_by_word(objid)

    def dump_object_cb(self, obj):
        self.__worddb.update_wordlist(obj)

    def add_words(self, words_iter, max_count=None):
        count = 0
        self.cursor.execute('PRAGMA synchronous=0;')

        while words_iter.has_data() and (max_count is None or count < max_count):
            word = words_iter.get()
            wle = self.get_object(word, cache_none=False)
            if wle is None:
                continue
            wle.incr()
            count += 1
            if count % 1000 == 0:
                print "Inserted", count, "words"
        self.flush()


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
