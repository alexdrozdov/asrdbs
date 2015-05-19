#!/usr/bin/env python
# -*- #coding: utf8 -*-


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

    def __grow_to(self, node, link):
        if self.__contains_nodes_group(node):
            return
        self.__links.append((node, self.__head, link))
        self.__head.append(node)
        self.__nodes.append(node)
        self.__checksum += node.get_uniq()
        self.__groups_csum += node.get_group().get_uniq()
        self.__links_csum += link.get_uniq()

    def __eval_target_groups(self):
        groups = {}
        for h in self.__head:
            if not h.has_links():
                return
            for node, link in h.get_links():
                if self.__contains_nodes_group(node):
                    continue
                g_uniq = node.get_group().get_uniq()
                if groups.has_key(g_uniq):
                    groups[g_uniq].append((node, link))
                else:
                    groups[g_uniq] = [(node, link), ]
        g_list = [v for v in groups.values()]
        return g_list

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
            for sl, _ in slaves:
                if (sl.get_uniq() & self.__links_csum) == 0:
                    continue
                if sl in predicates:
                    self.__has_subject_predicate = True
                    return

    def __iter_glist_entries(self, snakes, g_list, level, prev_vals):
        for node, link in g_list[level]:
            pv = [nl for nl in prev_vals]
            pv.append((node, link))
            if level == len(g_list)-1:
                snake = GraphSnake(snake=self)
                snakes.add_snake(snake)
                for p in pv:
                    snake.__grow_to(p[0], p[1])
                continue
            self.__iter_glist_entries(snakes, g_list, level+1, pv)

    def grow(self, snakes):
        if not len(self.__head):
            return

        g_list = self.__eval_target_groups()
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

    def build(self, entries):
        self.__init_snake_lists(entries)
        self.__grow_snakes()
        self.__remove_duplicate_snakes()
        self.__sort_snakes()
        self.__remove_incomplete_snakes()
        self.__find_subject_predicates()
        self.__sort_snakes()

        self.__snakes[0].print_entries()

        return self.__snakes

    def add_snake(self, snake):
        # print "add_snake"
        self.__snakes.append(snake)
        self.__snakes_qq.append(snake)

    def print_snakes_len(self):
        print "__snakes len=", len(self.__snakes)
        print "__snakes_qq len=", len(self.__snakes_qq)
