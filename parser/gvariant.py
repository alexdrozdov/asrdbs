#!/usr/bin/env python
# -*- #coding: utf8 -*-


class SequenceRuleMatcher(object):
    def __init__(self):
        self.__rules = []
        self.__name2rule = {}
        self.__create_rules()

    def __create_rules(self):
        self.add_rule(NounAdjSqRule())
        self.add_rule(LinkedNounSqRule())
        self.add_rule(SubjectPredicateSqRule())

    def add_rule(self, rule):
        if self.__name2rule.has_key(rule.get_rule_name()):
            raise ValueError("rule already exists")
        self.__rules.append(rule)
        self.__name2rule[rule.get_rule_name()] = rule

    def match_graph(self, graph):
        sqs = []
        sqs_names = {}
        for f in graph.get_forms():
            for r in self.__rules:
                if sqs_names.has_key(r.get_rule_name()):
                    sq = sqs_names[r.get_rule_name()]
                    res, new_sq = r.handle_form(sq, f)
                    if res:
                        if sq.is_complete():
                            sqs.append(sq)
                            sqs_names.pop(r.get_rule_name())
                        if len(new_sq):
                            sqs_names[r.get_rule_name()] = new_sq[0]
                    else:
                        sqs_names.pop(r.get_rule_name())
                else:
                    res, sq = r.handle_form(None, f)
                    if res:
                        sqs_names[r.get_rule_name()] = sq[0]
        for rule_name, sq in sqs_names.items():
            rule = self.__name2rule[rule_name]
            res, _ = rule.sentence_end(sq)
            if res:
                if sq.is_complete():
                    sqs.append(sq)

        graph.set_sequences(sqs)
        return sqs


class SequenceRule(object):
    def __init__(self, sq_rule_name):
        self.__rule_name = sq_rule_name

    def get_rule_name(self):
        return self.__rule_name


class NounAdjSqRule(SequenceRule):
    def __init__(self):
        SequenceRule.__init__(self, 'noun-adj_seq')

    def handle_form(self, sq, form):
        if sq is None:
            if not form.is_adjective():
                return False, []
            sq = NounAdjSequence(self.get_rule_name())
            sq.add_adjective(form)
            return True, [sq, ]
        if sq.is_complete():
            raise ValueError("Tried to process form while sequence is complete")
        if form.is_adjective():
            if sq.adj_is_capable(form):
                sq.add_adjective(form)
                return True, []
            else:
                sq.finalize(False)
                return False, []
        if form.is_noun():
            if sq.noun_is_capable(form):
                sq.set_noun(form)
                res, linked_adjectives = self.__validate_noun_linkage(sq)
                if not res:
                    sq.finalize(False)
                    return False, []

                sq.set_adjectives(linked_adjectives)
                self.__remove_unwanted_links(sq)
                sq.finalize(True)
                return True, []

        sq.finalize(False)
        return False, []

    def __validate_noun_linkage(self, sq):
        linked_adjectives = []
        for a in sq.get_adjectives():
            if sq.get_noun() in a.get_master_forms():
                linked_adjectives.append(a)
                continue
            if len(linked_adjectives):
                return False, []
        if not len(linked_adjectives):
            return False, []
        return True, linked_adjectives

    def __remove_unwanted_links(self, sq):
        for a in sq.get_adjectives():
            for master, link in a.get_masters():
                if master != sq.get_noun():
                    sq.add_unwanted_link(link)

    def sentence_end(self, sq):
        return False, []


class LinkedNounSqRule(SequenceRule):
    def __init__(self):
        SequenceRule.__init__(self, 'noun_seq')

    def __validate_linkage(self, sq):
        nouns = sq.get_nouns()
        prev_noun = nouns[0]
        # linked_nouns = [prev_noun, ]
        for noun in nouns[1:]:
            if prev_noun in noun.get_master_forms():
                # linked_nouns.append(noun)
                continue
            return False
        return True

    def __finalize_sequence(self, sq):
        nouns = sq.get_nouns()
        prev_noun = nouns[0]
        for noun in nouns[1:]:
            for master, link in noun.get_masters():
                if master != prev_noun:
                    sq.add_unwanted_link(link)
            prev_noun = noun
        sq.finalize(True)

    def handle_form(self, sq, form):
        if sq is None:
            if not form.is_noun():
                return False, []
            sq = NounSequence(self.get_rule_name())
            sq.add_noun(form)
            return True, [sq, ]
        if sq.is_complete():
            raise ValueError("Tried to process form while sequence is complete")
        if form.is_verb():
            if sq.noun_count() > 1 and self.__validate_linkage(sq):
                self.__finalize_sequence(sq)
                return True, []
            sq.finalize(False)
            return False, []
        if form.is_noun():
            if sq.is_capable(form):
                sq.add_noun(form)
                return True, []
            if sq.noun_count() > 1 and self.__validate_linkage(sq):
                self.__finalize_sequence(sq)
            sq = NounSequence(self.get_rule_name())
            sq.add_noun(form)
            return True, [sq, ]
        return True, []

    def sentence_end(self, sq):
        if sq.noun_count() > 1 and self.__validate_linkage(sq):
            self.__finalize_sequence(sq)
            return True, []
        sq.finalize(False)
        return False, []


class SubjectPredicateSqRule(SequenceRule):
    def __init__(self):
        SequenceRule.__init__(self, 'subject-predicate_seq')

    def __validate_linkage(self, sq):
        nouns = sq.get_nouns()
        prev_noun = nouns[0]
        # linked_nouns = [prev_noun, ]
        for noun in nouns[1:]:
            if prev_noun in noun.get_master_forms():
                # linked_nouns.append(noun)
                continue
            return False
        return True

    def __finalize_sequence(self, sq):
        subjects = sq.get_subjects()
        for s in subjects:
            for master, link in s.get_masters():
                sq.add_unwanted_link(link)
        for p in sq.get_predicates():
            for master, link in p.get_masters():
                if master not in subjects:
                    sq.add_unwanted_link(link)
        sq.finalize(True)

    def __form_is_subject(self, form):
        if not form.is_noun() and not form.is_pronoun():
            return False
        if form.get_case() == 'nominative':
            return True
        return False

    def __form_is_predicate(self, form):
        return form.is_verb()

    def handle_form(self, sq, form):
        if sq is None:
            if not self.__form_is_subject(form) and not self.__form_is_predicate(form):
                return False, []
            sq = SubjectPredicateSequence(self.get_rule_name())
            sq.add_form(form)
            return True, [sq, ]

        if sq.is_complete():
            raise ValueError("Tried to process form while sequence is complete")

        if not self.__form_is_subject(form) and not self.__form_is_predicate(form):
            return True, []

        if self.__form_is_predicate(form):
            if sq.predicate_is_first() and sq.has_subject():  # We couldnt add another predicate after subject was added
                self.__finalize_sequence(sq)
                sq = SubjectPredicateSequence(self.get_rule_name())
                sq.add_form(form)
                return True, [sq, ]

        if self.__form_is_subject(form):
            if sq.subject_is_first() and sq.has_predicate():  # We couldnt add another predicate after subject was added
                self.__finalize_sequence(sq)
                sq = SubjectPredicateSequence(self.get_rule_name())
                sq.add_form(form)
                return True, [sq, ]

        if sq.is_capable(form):
            sq.add_form(form)
            return True, []

        if sq.is_skipable(form):
            return True, []

        if sq.has_subject() and sq.has_predicate():
            self.__finalize_sequence(sq)
            sq = SubjectPredicateSequence(self.get_rule_name())
            sq.add_form(form)
            return True, [sq, ]
        sq.finalize(False)
        return False, []

    def sentence_end(self, sq):
        if sq.has_subject() and sq.has_predicate():
            self.__finalize_sequence(sq)
            return True, []
        sq.finalize(False)
        return False, []


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
        if self.__gender == form.get_gender() and self.__count == form.get_count() and self.__case == form.get_case():
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
            self.__gender = adj.get_gender()
            self.__count = adj.get_count()
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
            if self.__time is None and self.__count is None:
                return True
            if self.__time == form.get_time() and self.__count == form.get_count():
                return True
        return False

    def is_skipable(self, form):
        if not form.is_verb():
            return True
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

    def build(self, entries):
        self.__init_snake_lists(entries)
        self.__grow_snakes()
        self.__make_lost_internal_links()
        self.__remove_duplicate_snakes()
        self.__sort_snakes()
        self.__remove_incomplete_snakes()
        self.__find_subject_predicates()
        self.__sort_snakes()

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
