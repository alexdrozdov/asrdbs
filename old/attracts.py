#!/usr/bin/env python
# -*- #coding: utf8 -*-


import groups
import traceback


class PartOfSpeechComparatorSelector(object):
    def __init__(self):
        self.comp_dict = {}

    def add_comparator(self, pos1_name, pos2_name, comparator):
        self.__add_cmp(pos1_name, pos2_name, comparator)
        self.__add_cmp(pos2_name, pos1_name, comparator)

    def __add_cmp(self, p1, p2, comparator):
        if p1 in self.comp_dict:
            d = self.comp_dict[p1]
        else:
            d = self.comp_dict[p1] = {}
        d[p2] = comparator

    def get_comparator(self, pos1_name, pos2_name):
        try:
            return self.comp_dict[pos1_name][pos2_name]
        except:
            return None


pcs = PartOfSpeechComparatorSelector()


class NounAdjective(object):
    def __init__(self):
        pass

    def __noun_adj(self, wf1, wf2):
        if wf1.get_pos() == 'noun':
            return wf1, wf2
        return wf2, wf1

    def compare(self, wf1, wf2):
        noun, adj = self.__noun_adj(wf1, wf2)
        res = 0.0
        try:
            if noun.get_gender() != adj.get_gender():
                return 0.0
            res += 1.0
        except:
            pass
        try:
            if noun.get_count() != adj.get_count():
                return 0.0
            res += 1.0
        except:
            pass
        try:
            if noun.get_case() != adj.get_case():
                return 0.0
            res += 1.0
        except:
            pass
        return res / 3.0

    def make_link(self, wf1, wf2):
        noun, adj = self.__noun_adj(wf1, wf2)
        wl = WordLink(noun, adj, type(self), 1.0)

        noun.attracts.append(wl)
        adj.attracted.append(wl)


class VerbNoun(object):
    def __init__(self):
        pass

    def __verb_noun(self, wl1, wl2):
        if wl1.get_pos() == 'verb':
            return wl1, wl2
        return wl2, wl1

    def compare(self, wl1, wl2):
        # Let it always match - graph will try to separate words
        try:
            verb, noun = self.__verb_noun(wl1, wl2)
            if verb.get_time() == 'infinite' and noun.get_case() == 'nominative':
                return False   # лететь птица - недопустимо
            if verb.get_time() == 'past' and noun.get_case() == 'nominative' and verb.get_gender() != noun.get_gender():
                return False   # доил коза - тоже не скажешь, а вот козел доил окрестные палатки =)
            return True
        except:
            print(traceback.format_exc())
            print(wl1.get_word(), wl2.get_word())
            return False

    def make_link(self, wf1, wf2):
        verb, noun = self.__verb_noun(wf1, wf2)
        if noun.get_case() == 'nominative':
            wl = WordLink(noun, verb, type(self), 1.0)
            noun.attracts.append(wl)
            verb.attracted.append(wl)
        else:
            wl = WordLink(verb, noun, type(self), 1.0)
            verb.attracts.append(wl)
            noun.attracted.append(wl)


class VerbAdverb(object):
    def __init__(self):
        pass

    def compare(self, info1, info2):
        return True


class AdverbAdjective(object):
    def __init__(self):
        pass

    def compare(self, info1, info2):
        return True


class PrepositionNoun(object):
    def __init__(self):
        pass

    def __preposition_noun(self, wf1, wf2):
        if wf1.get_pos() == 'preposition':
            return wf1, wf2
        return wf2, wf1

    def compare(self, wf1, wf2):
        prep, noun = self.__preposition_noun(wf1, wf2)
        if prep.get_position() > noun.get_position():
            return False  # Prepostion cant stand after noun. Really, cap
        if prep.attracts.closed:
            return False
        try:
            if prep.get_case() == noun.get_case():
                return True
        except:
            pass
        return False

    def make_link(self, wf1, wf2):
        prep, noun = self.__preposition_noun(wf1, wf2)
        wl = WordLink(prep, noun, type(self), 1.0)

        prep.attracts.append(wl)
        prep.attracts.close()
        noun.attracted.append(wl)


class VerbVerb(object):
    def __init__(self):
        pass

    def compare(self, info1, info2):
        if 'time' not in info1 or not info2.has_key['time']:
            return False
        if info1['time'] != info2['time'] and (info1['time'] == 'infinite' or info2['time'] == 'infinite'):
            return True
        return False


class NounNoun(object):
    def __init__(self):
        pass

    def check_restricts(self, wf1, wf2):
        g1 = wf1.get_group()
        g2 = wf2.get_group()
        g = g2.left
        restrict = {"parts_of_speech": "noun"}
        while g is not None and g != g1:
            if g.has_spec(restrict):
                print("restricting")
                return False
            g = g.left
        return True

    def compare(self, wf1, wf2):
        if wf1.get_case() == 'nominative' and wf2.get_case() == 'nominative':
            return False
        if wf1.get_case() == 'nominative' and wf2.get_case() != 'nominative':
            if wf1.get_position() < wf2.get_position():
                return self.check_restricts(wf1, wf2)
            return False
        if wf1.get_case() != 'nominative' and wf2.get_case() == 'nominative':
            if wf2.get_position() < wf1.get_position():
                return self.check_restricts(wf2, wf1)
            return False
        return self.check_restricts(wf1, wf2)

    def make_link(self, wf1, wf2):
        if wf1.get_case() == 'nominative' or wf1.get_position() < wf2.get_position():
            wf_master = wf1
            wf_slave = wf2
        else:
            wf_master = wf2
            wf_slave = wf1
        wl = WordLink(wf_master, wf_slave, type(self), 1.0)

        wf_master.attracts.append(wl)
        wf_slave.attracted.append(wl)


na_comp = NounAdjective()
pn_comp = PrepositionNoun()
vn_comp = VerbNoun()
nn_comp = NounNoun()
pcs.add_comparator('noun', 'adjective', na_comp)
pcs.add_comparator('preposition', 'noun', pn_comp)
pcs.add_comparator('verb', 'noun', vn_comp)
pcs.add_comparator('noun', 'noun', nn_comp)


class WordForm(object):
    def __init__(self, form, primary, forms):
        self.form = form
        self.primary = primary
        self.forms = forms
        self.info = eval(self.form['info'])

    def get_pos(self):
        return self.info['parts_of_speech']

    def get_case(self):
        return self.info['case']

    def get_gender(self):
        return self.info['gender']

    def get_count(self):
        return self.info['count']

    def get_time(self):
        return self.info['time']

    def get_word(self):
        return self.form['word']

    def spec_cmp(self, spec, ignore_missing=False):
        for k, v in list(spec.items()):
            if k in self.info:
                if self.info[k] == v:
                    continue
                return False
            if ignore_missing:
                continue
            return False
        return True


class WordLink(object):
    def __init__(self, frm, to, ltype, weight):
        self.frm = frm
        self.to = to
        self.ltype = ltype
        self.weight = weight


class AttractionList(object):
    def __init__(self):
        self.entries = []
        self.closed = False

    def append(self, link):
        if self.closed:
            return
        self.entries.append(link)

    def close(self):
        self.closed = True

    def __len__(self):
        return len(self.entries)


class PathTo(object):
    def __init__(self, frm_wfn):
        self.left_targets = {}
        self.right_targets = {}
        self.group = frm_wfn.get_group()

    def add_word_node(self, wfn):
        l = self.group.left
        tmp_path = []
        while l is not None:
            if l.contains_word_node(wfn):
                self.left_targets[wfn] = tmp_path
                return
            tmp_path.append(l)
            l = l.left
        r = self.group.right
        tmp_path = []
        while r is not None:
            if r.contains_word_node(wfn):
                self.right_targets[wfn] = tmp_path
                return
            tmp_path.append(r)
            r = r.right

    def path_to(self, to):
        if to in self.left_targets:
            return self.left_targets[to]
        if to in self.right_targets:
            return self.right_targets[to]
        return []

    def path_to_contains(self, to, spec):
        for p in self.path_to(to):
            pass

    def distance_to(self, to):
        return len(self.path_to(to))

    def is_lefter(self, to):
        return to in self.left_targets

    def is_righter(self, to):
        return to in self.right_targets


class WordFormNode(WordForm):
    def __init__(self, form, primary, forms, position):
        WordForm.__init__(self, form, primary, forms)
        self.position = position
        self.attracts = AttractionList()
        self.attracted = AttractionList()
        self.group = None

    def set_group(self, group):
        self.group = group

    def get_group(self):
        return self.group

    def get_position(self):
        return self.position

    def get_accessable_groups(self):
        groups = []
        for wl in self.attracts.entries:
            linked_wfn = wl.to
            group = linked_wfn.get_group()
            if group not in groups:
                groups.append(group)
        for wl in self.attracted.entries:
            linked_wfn = wl.frm
            group = linked_wfn.get_group()
            if group not in groups:
                groups.append(group)
        return groups

    def has_attractions(self):
        if len(self.attracts) > 0 or len(self.attracted) > 0:
            return True
        return False


class WordFormNodeGroup(object):
    def __init__(self, word_forms, left, right):
        self.nodes = word_forms
        for wf in word_forms:
            wf.set_group(self)
        self.left = left
        self.right = right
        if self.left is not None:
            self.left.right = self
        if self.right is not None:
            self.right.left = self

    def attract(self, other_wfng):
        for my_wfn in self.nodes:
            try:
                my_pos = my_wfn.get_pos()
            except:
                print(traceback.format_exc())
                continue

            for other_wfn in other_wfng.nodes:
                try:
                    other_pos = other_wfn.get_pos()
                except:
                    print(traceback.format_exc())
                    continue
                comp = pcs.get_comparator(my_pos, other_pos)
                if comp is None:
                    continue

                if comp.compare(my_wfn, other_wfn):
                    print(my_pos, my_wfn.get_word(), other_pos, other_wfn.get_word())
                    comp.make_link(my_wfn, other_wfn)

    def get_accessable_groups(self):
        groups = []
        for n in self.nodes:
            groups.extend(n.get_accessable_groups())
        groups = [g for g in set(groups)]
        return groups

    def has_attractions(self):
        for n in self.nodes:
            if n.has_attractions():
                return True
        return False

    def contains_word_node(self, wfn):
        if wfn in self.nodes:
            return True
        return False

    def has_spec(self, spec, ignore_missing=False):
        for wfn in self.nodes:
            if wfn.spec_cmp(spec, ignore_missing):
                return True
        return False


class WordFormFabric(object):
    def __init__(self):
        pass

    def create(self, word, position, left_group, right_group):
        res = []
        info = groups.db.get_word_info(word)
        self.variants = []
        for i in info:
            form = i['form']
            forms = i['forms']
            primary = i['primary']
            for f in form:
                res.append(WordFormNode(f, primary, forms, position))
        return WordFormNodeGroup(res, left_group, right_group)


class SentenceAttractors(object):
    def __init__(self, sentence):
        self.s = sentence
        self.entries = []
        wff = WordFormFabric()
        word_position = 0
        prev_wfng = None
        for w in self.s:
            wfng = wff.create(w, word_position, prev_wfng, None)
            for e in self.entries:
                wfng.attract(e)
            self.entries.append(wfng)
            word_position += 1
            prev_wfng = wfng
        if not self.validate_complete_attraction():
            print("Error - not all leafs are attracted")
        if not self.validate_group_linkage():
            print("Error - graph is not completely linked")

    def validate_complete_attraction(self):
        for e in self.entries:
            if not e.has_attractions():
                return False
        return True

    def validate_group_linkage(self):
        unknown = [e for e in self.entries[1:]]
        accessable = [self.entries[0]]
        finalized = []
        while len(accessable) > 0:
            e = accessable.pop()
            acc = e.get_accessable_groups()
            for a in acc:
                if a not in unknown:
                    continue
                accessable.append(a)
                unknown.remove(a)
            finalized.append(e)
        if len(unknown) > 0:
            return False
        return True

    def attract(self):
        for e in self.entries:
            for ee in self.entries:
                if e != ee:
                    e.check_attract(ee)


sentence = ['падал', 'прошлогодний', 'снег', 'на', 'теплую', 'землю', 'поля']

sa = SentenceAttractors(sentence)
# sa.attract()
