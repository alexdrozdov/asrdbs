#!/usr/bin/env python
# -*- #coding: utf8 -*-


class SequenceRule(object):
    def __init__(self, sq_rule_name):
        self.__rule_name = sq_rule_name

    def get_rule_name(self):
        return self.__rule_name


class Sequence(object):
    def __init__(self, rule_name):
        self.__rule_name = rule_name
        self.__is_complete = False
        self.__is_valid = True
        self.__required_links = []
        self.__unwanted_links = []

    def get_rule_name(self):
        return self.__rule_name

    def is_complete(self):
        return self.__is_complete

    def is_valid(self):
        return self.__is_valid

    def finalize(self, valid):
        self.__is_complete = True
        self.__is_valid = valid

    def print_sequence(self):
        raise ValueError()

    def add_unwanted_link(self, link):
        if link not in self.__unwanted_links:
            self.__unwanted_links.append(link)

    def add_required_link(self, link):
        if link not in self.__required_links:
            self.__required_links.append(link)

    def get_unwanted_links(self):
        return self.__unwanted_links


class NounAdjSequence(Sequence):
    def __init__(self, rule_name):
        Sequence.__init__(self, rule_name)
        self.__noun = None
        self.__adjectives = []
        self.__case = None
        self.__count = None
        self.__gender = None

    def __check_capability(self, form):
        if self.__gender is None and self.__case is None and self.__count is None:
            return True
        if self.__count == 'singilar' and form.get_count() == 'singilar':
            if self.__gender == form.get_gender() and self.__count == form.get_count() and self.__case == form.get_case():
                return True
        else:
            if self.__count == form.get_count() and self.__case == form.get_case():
                return True
        return False

    def set_noun(self, noun):
        if not len(self.__adjectives):
            raise ValueError("Tried to set noun while adjectives are undefined")
        self.__noun = noun

    def add_adjective(self, adj):
        if not self.__check_capability(adj):
            raise ValueError("Adjective form is incompatible with previously set adjectives")
        if not self.has_adjectives():
            self.__count = adj.get_count()
            if self.__count == 'singilar':
                self.__gender = adj.get_gender()
            self.__case = adj.get_case()
        self.__adjectives.append(adj)

    def has_noun(self):
        return self.__noun is not None

    def has_adjectives(self):
        return len(self.__adjectives) > 0

    def adj_is_capable(self, adj):
        return self.__check_capability(adj)

    def noun_is_capable(self, noun):
        return self.__check_capability(noun)

    def get_last_adjective(self):
        return self.__adjectives[-1]

    def get_adjectives(self):
        return self.__adjectives

    def get_noun(self):
        return self.__noun

    def set_adjectives(self, adjectives):
        self.__adjectives = adjectives

    def print_sequence(self):
        print self.get_rule_name(),
        for a in self.__adjectives:
            print a.get_word(),
        print self.get_noun().get_word()


class NounSequence(Sequence):
    def __init__(self, rule_name):
        Sequence.__init__(self, rule_name)
        self.__nouns = []

    def is_capable(self, noun):
        if not len(self.__nouns):
            return True
        last_noun = self.__nouns[-1]
        if last_noun in noun.get_master_forms():
            return True
        return False

    def add_noun(self, noun):
        # print "add_noun",
        # for n in self.__nouns:
        #     print n.get_word(),
        # print noun.get_word()
        self.__nouns.append(noun)

    def noun_count(self):
        return len(self.__nouns)

    def get_nouns(self):
        return self.__nouns

    def print_sequence(self):
        print self.get_rule_name(),
        for n in self.__nouns:
            print n.get_word(),
        print ""


class NounPronounSequence(Sequence):
    def __init__(self, rule_name):
        Sequence.__init__(self, rule_name)
        self.__noun = None
        self.__pronoun = None

    def is_capable(self, entry):
        if entry.is_pronoun() and entry.get_case() == 'nominative':
            return False
        if self.__noun is None and self.__pronoun is None:
            return True
        if entry.is_noun():
            if self.__noun is not None:
                return False
            if entry not in self.__pronoun.get_master_forms():
                return False
            return True
        if entry.is_pronoun():
            if self.__pronoun is not None:
                return False
            if self.__noun not in entry.get_master_forms():
                return False
            return True
        return False

    def add_form(self, form):
        if form.is_noun():
            self.add_noun(form)
        elif form.is_pronoun():
            self.add_pronoun(form)
        else:
            raise ValueError('Neither pronoun nor noun ' + form.get_pos())

    def add_noun(self, noun):
        self.__noun = noun

    def add_pronoun(self, pronoun):
        self.__pronoun = pronoun

    def get_noun(self):
        return self.__noun

    def get_pronoun(self):
        return self.__pronoun

    def print_sequence(self):
        print self.get_rule_name(),
        print self.__noun.get_word(), self.__pronoun.get_word()


class AdverbAdjSequence(Sequence):
    def __init__(self, rule_name):
        Sequence.__init__(self, rule_name)
        self.__adverb = None
        self.__adjective = None

    def __check_capability(self, form):
        if self.__gender is None and self.__case is None and self.__count is None:
            return True
        if self.__count == 'singilar':
            if self.__gender == form.get_gender() and self.__count == form.get_count() and self.__case == form.get_case():
                return True
        else:
            if self.__count == form.get_count() and self.__case == form.get_case():
                return True
        return False

    def is_capable(self, adj):
        return adj in self.__adverb.get_master_forms()

    def set_adverb(self, adverb):
        self.__adverb = adverb

    def set_adjective(self, adjective):
        self.__adjective = adjective

    def get_adjective(self):
        return self.__adjective

    def get_adverb(self):
        return self.__adverb

    def print_sequence(self):
        print self.get_rule_name(),
        print self.get_adverb().get_word(), self.get_adjective().get_word()


class VerbSplitterSequence(Sequence):
    def __init__(self, rule_name):
        Sequence.__init__(self, rule_name)
        self.__groups = []
        self.__current_group = None

    def is_capable(self, noun):
        return True

    def add_form(self, form):
        if self.__current_group is not None:
            self.__current_group.append(form)
        else:
            self.__current_group = [form, ]

    def add_verb(self, verb=None):
        self.close_current()

    def group_count(self):
        l = len(self.__groups)
        if self.__current_group is not None:
            l += 1
        return l

    def close_current(self):
        if self.__current_group is not None:
            self.__groups.append(self.__current_group)
        self.__current_group = None

    def get_groups(self):
        return self.__groups

    def print_sequence(self):
        pass


class SubjectPredicateSequence(Sequence):
    def __init__(self, rule_name):
        Sequence.__init__(self, rule_name)
        self.__subjects = []
        self.__predicates = []
        self.__subject_is_first = None
        self.__time = None
        self.__count = None

    def is_capable(self, form):
        if form.get_pos() == 'noun':
            return True
        if form.get_pos() == 'verb':
            if not form.has_property('time'):
                return False
            if self.__time is None and self.__count is None:
                return True
            if self.__time == form.get_time() and self.__count == form.get_count():
                return True
        return False

    def is_skipable(self, form):
        if not form.is_verb():
            return True
        if not form.has_property('time'):
            return False
        if form.get_time() == 'infinitive':
            return True
        return False

    def predicate_is_first(self):
        return not self.__subject_is_first

    def subject_is_first(self):
        return self.__subject_is_first

    def add_subject(self, form):
        if self.__subject_is_first is None and len(self.__subjects) == 0 and len(self.__predicates) == 0:
            self.__subject_is_first = True
        self.__subjects.append(form)

    def add_predicate(self, form):
        if not form.has_property('time'):
            raise ValueError("Tried to add wrong verb")
        if self.__subject_is_first is None and len(self.__subjects) == 0 and len(self.__predicates) == 0:
            self.__subject_is_first = False
            self.__time = form.get_time()
            self.__count = form.get_count()
        self.__predicates.append(form)

    def add_form(self, form):
        if form.is_verb():
            self.add_predicate(form)
            return
        self.add_subject(form)

    def has_subject(self):
        return len(self.__subjects) > 0

    def has_predicate(self):
        return len(self.__predicates) > 0

    def get_subjects(self):
        return self.__subjects

    def get_predicates(self):
        return self.__predicates

    def print_sequence(self):
        print self.get_rule_name(),
        for s in self.__subjects:
            print s.get_word(),
        for p in self.__predicates:
            print p.get_word(),
        print ''


class PatternRuntime(object):
    def __init__(self):
        pass


class FormGraph(object):
    def __init__(self):
        self.__forms = []
        self.__links = []
        self.__links_csum = 0
        self.__forms_csum = 0
        self.__uniq2form = {}
        self.__uniq2link = {}
        self.__sequences = []

    def clone_form(self, form):
        f = form.clone_without_links()
        self.__forms.append(f)
        self.__forms.sort(key=lambda frm: frm.get_position())
        self.__forms_csum |= f.get_uniq()
        self.__uniq2form[f.get_uniq()] = f

    def clone_link(self, link):
        l = link.clone_without_links()
        master = self.__uniq2form[link.get_master().get_uniq()]
        slave = self.__uniq2form[link.get_slave().get_uniq()]

        l.set_ms(master=master, slave=slave)

        self.__links.append(l)
        self.__links_csum |= l.get_uniq()
        master.add_slave(l, slave)
        slave.add_master(l, master)

    def __delete_link(self, link):
        self.__links.remove(link)
        self.__links_csum &= ~link.get_uniq()
        master = link.get_master()
        slave = link.get_slave()
        slave.remove_master(master)
        master.remove_slave(slave)

    def get_forms(self):
        return self.__forms

    def print_graph(self):
        for f in self.__forms:
            print f.get_word(),
        print ""

    def set_sequences(self, sequences):
        self.__sequences = sequences

    def __link_is_exclusive(self, link):
        master = link.get_master()
        slave = link.get_slave()
        if master.get_link_count() == 1:
            return True
        if slave.get_link_count() == 1:
            return True

    def __remove_exclusive_unlinks(self):
        sqs = []
        for s in self.__sequences:
            applicable = True
            ulinks = s.get_unwanted_links()
            for ulink in ulinks:
                if self.__link_is_exclusive(ulink):
                    applicable = False
                    break
            if not applicable:
                continue
            sqs.append(s)
        self.__sequences = sqs

    def __remove_unwanted_links(self):
        ulinks = []
        for s in self.__sequences:
            ulinks.extend(s.get_unwanted_links())
        ulinks = list(set(ulinks))
        for link in ulinks:
            self.__delete_link(link)

    def apply_sequences(self):
        self.__remove_exclusive_unlinks()
        self.__remove_unwanted_links()

    def has_link(self, link):
        if link.get_uniq() & self.__links_csum:
            return True
        return False

    def has_form(self, form):
        if form.get_uniq() & self.__forms_csum:
            return True
        return False


class GraphSnake(object):

    subject_bonus = 10
    predicate_bonus = 10
    subject_predicate_bonus = 20

    def __init__(self, snake=None, node=None):
        self.__has_subject = False
        self.__has_predicate = False
        self.__has_subject_predicate = False
        self.__score = 0

        if snake is not None:
            self.__init_from_snake(snake)
            return
        if node is not None:
            self.__init_from_node(node)
            return
        raise ValueError("snake or node param is required")

    def __init_from_snake(self, snake):
        self.__head = [h for h in snake.__head]
        self.__nodes = [n for n in snake.__nodes]
        self.__links = [l for l in snake.__links]
        self.__checksum = snake.__checksum
        self.__groups_csum = snake.__groups_csum
        self.__links_csum = snake.__links_csum

    def __init_from_node(self, node):
        self.__head = [node, ]
        self.__nodes = [node, ]
        self.__checksum = node.get_uniq()
        self.__groups_csum = node.get_group().get_uniq()
        self.__links_csum = 0
        self.__links = []

    def __contains_nodes_group(self, node):
        g = node.get_group()
        if (self.__groups_csum & g.get_uniq()) == 0:
            return False
        return True

    def can_grow(self):
        for head in self.__head:
            if not head.has_links():
                continue
            possible_links = head.get_links()
            for p in possible_links:
                if not self.__contains_nodes_group(p[0]):
                    return True
        return False

    def __grow_to(self, node, link, src_node):
        if self.__contains_nodes_group(node):
            return
        self.__links.append((node, src_node, link))
        self.__head.append(node)
        self.__nodes.append(node)
        self.__checksum += node.get_uniq()
        self.__groups_csum += node.get_group().get_uniq()
        self.__links_csum += link.get_uniq()

    def __eval_target_groups(self, head):
        groups = {}
        for h in head:
            if not h.has_links():
                continue
            for node, link in h.get_links():
                if self.__contains_nodes_group(node):
                    continue
                g_uniq = node.get_group().get_uniq()
                if groups.has_key(g_uniq):
                    groups[g_uniq].append((node, link, h))
                else:
                    groups[g_uniq] = [(node, link, h), ]
        g_list = [v for v in groups.values()]
        return g_list

    def make_internal_links(self):
        for n in self.__nodes:
            if not n.has_links():
                continue
            for node, link in n.get_links():
                if not self.has_form(node):
                    continue
                if self.has_link(link):
                    continue
                self.__links.append((node, n, link))
                self.__links_csum += link.get_uniq()

    def __find_subject_predicate(self):
        subjects = []
        predicates = []
        for n in self.__nodes:
            if n.is_subject():
                self.__has_subject = True
                subjects.append(n)
            if n.is_predicate():
                self.__has_predicate = True
                predicates.append(n)

        for s in subjects:
            slaves = s.get_slaves()
            for sl, l in slaves:
                if (l.get_uniq() & self.__links_csum) == 0:
                    continue
                if sl in predicates:
                    self.__has_subject_predicate = True
                    return

    def __iter_glist_entries(self, snakes, g_list, level, prev_vals):
        for node, link, src_node in g_list[level]:
            pv = [nl for nl in prev_vals]
            pv.append((node, link, src_node))
            if level == len(g_list)-1:
                snake = GraphSnake(snake=self)
                snakes.add_snake(snake)
                for p in pv:
                    snake.__grow_to(p[0], p[1], p[2])
                continue
            self.__iter_glist_entries(snakes, g_list, level+1, pv)

    def grow(self, snakes):
        if not len(self.__head):
            return

        g_list = self.__eval_target_groups(self.__head)
        self.__head = []
        self.__iter_glist_entries(snakes, g_list, 0, [])

    def get_csum(self):
        return self.__checksum

    def get_groups_csum(self):
        return self.__groups_csum

    def get_links_csum(self):
        return self.__links_csum

    def print_entries(self):
        for n in self.__nodes:
            print n.get_word(),
        print 'csum={0}, groups={1}, links={2}, score={3}'.format(self.__checksum, self.__groups_csum, self.__links_csum, self.__score)

    def __eval_score(self):
        if self.__has_subject:
            self.__score += GraphSnake.subject_bonus
        if self.__has_predicate:
            self.__score += GraphSnake.predicate_bonus
        if self.__has_subject_predicate:
            self.__score += GraphSnake.subject_predicate_bonus

    def get_score(self):
        return self.__score

    def find_subject_predicate(self):
        self.__find_subject_predicate()
        self.__eval_score()
        # print self.__has_subject, self.__has_predicate, self.__has_subject_predicate

    def has_link(self, link):
        if link.get_uniq() & self.__links_csum:
            return True
        return False

    def has_form(self, form):
        if form.get_uniq() & self.__checksum:
            return True
        return False

    def snake_to_graph(self):
        fg = FormGraph()
        for node in self.__nodes:
            fg.clone_form(node)
        for _, _, link in self.__links:
            fg.clone_link(link)
        return fg

    def add_syntax_node(self, node):
        self.__nodes.append(node)
        self.__checksum += node.get_uniq()
        self.__groups_csum += node.get_group().get_uniq()

    def __cmp__(self, other):
        if self.__score != other.__score:
            return -cmp(self.__score, other.__score)
        return -cmp(self.__groups_csum, other.__groups_csum)

    def __eq__(self, other):
        return self.__checksum == other.__checksum and self.__groups_csum == other.__groups_csum and self.__links_csum == other.__links_csum

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '{0}:{1}:{2}'.format(self.__checksum, self.__groups_csum, self.__links_csum)

    def __hash__(self):
        return hash(self.__repr__())


class GraphSnakes(object):
    def __init__(self):
        self.__snakes = []
        self.__snakes_qq = []

    def __init_snake_lists(self, entries):
        for e in entries:
            forms = e.get_forms()
            if not len(forms):
                continue
            if forms[0].is_syntax():
                continue
            for f in e.get_forms():
                snake = GraphSnake(node=f)
                self.__snakes.append(snake)
                self.__snakes_qq.append(snake)

    def __grow_snakes(self):
        while len(self.__snakes_qq):
            snake = self.__snakes_qq[0]
            self.__snakes_qq = self.__snakes_qq[1:]
            # snake.print_entries()
            # return
            if snake.can_grow():
                snake.grow(self)
            if snake.can_grow():
                self.__snakes_qq.append(snake)

    def __remove_duplicate_snakes(self):
        ss = set(self.__snakes)
        self.__snakes = list(ss)

    def __sort_snakes(self):
        self.__snakes.sort()

    def __remove_incomplete_snakes(self):
        max_groups = self.__snakes[0].get_groups_csum()
        snakes = []
        for s in self.__snakes:
            if s.get_groups_csum() == max_groups:
                snakes.append(s)
            else:
                break
        self.__snakes = snakes

    def __find_subject_predicates(self):
        for s in self.__snakes:
            s.find_subject_predicate()

    def __make_lost_internal_links(self):
        for s in self.__snakes:
            s.make_internal_links()

    def __add_syntax(self, entries):
        syntax_nodes = []
        for e in entries:
            forms = e.get_forms()
            if not len(forms):
                continue
            if not forms[0].is_syntax():
                continue
            syntax_nodes.append(forms[0])
        for s in self.__snakes:
            for n in syntax_nodes:
                s.add_syntax_node(n)

    def build(self, entries):
        self.__init_snake_lists(entries)
        self.__grow_snakes()
        self.__make_lost_internal_links()
        self.__remove_duplicate_snakes()
        self.__sort_snakes()
        self.__remove_incomplete_snakes()
        self.__find_subject_predicates()
        self.__sort_snakes()
        self.__add_syntax(entries)

        for s in self.__snakes:
            s.print_entries()

        return self.__snakes

    def add_snake(self, snake):
        # print "add_snake"
        self.__snakes.append(snake)
        self.__snakes_qq.append(snake)

    def export_graphs(self):
        graphs = []
        for s in self.__snakes:
            g = s.snake_to_graph()
            graphs.append(g)
        return graphs

    def print_snakes_len(self):
        print "__snakes len=", len(self.__snakes)
        print "__snakes_qq len=", len(self.__snakes_qq)
