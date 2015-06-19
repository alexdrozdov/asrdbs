#!/usr/bin/env python
# -*- coding: utf-8 -*-


import worddb


class WordPos(object):
    def __init__(self, parent, start_time, node):
        self.__parent = parent
        self.__start_time = start_time
        self.__node = node
        self.__accum_probability = 0.0
        self.__active_duration = 0.0
        self.__current_time = start_time
        self.__rel_probability = 0.0

        self.__pending_probability = 0.0
        self.__pending_time = 0.0

        self.__children = []

        if parent is not None:
            parent.__children.append(self)

    def fork(self, e):
        for c in self.__children:
            if c.is_same(e):
                return [c]

        forks = []
        cross_links = self.__node.get_subletter_links(e.get_letter())
        for cl in cross_links:
            node = self.__node.get_child(cl)
            wp = WordPos(self, self.__start_time, node)
            forks.append(wp)
        return forks

    def __update_probability(self, e, all_e):
        if self.__pending_time < e.end() and self.__pending_probability < e.probability():
            self.__pending_time = e.end()
            self.__pending_probability = e.probability()

    def update_probability(self, e, all_e):
        self.__update_probability(e, all_e)
        for c in self.__children:
            c.__update_probability(e, all_e)

    def commit_probabilities(self):
        self.__current_time = self.__pending_time
        self.__accum_probability += self.__pending_probability
        if self.__current_time - self.__start_time > 0.0:
            self.__rel_probability = self.__accum_probability / (self.__current_time - self.__start_time)
        else:
            self.__rel_probability = 0.0

    def eval_reliability(self, time):
        if time < self.__current_time:
            return self.__rel_probability

        return self.__rel_probability / (time - self.__current_time) * self.get_belive_interval()
        # get_belive_interval depends on symbol, pos and speech tone. Evalute it dinamicaly
        # May be its necessary to work with multiple flows for speech tones and
        # forks for any doubt

    def is_same(self, e):
        if self.__node.get_letter() == e.get_letter():
            return True
        return False

    def is_forkable(self, e):
        if self.__node.has_subletter(e.get_letter()) and self.__node.get_letter() != e.get_letter():
            return True
        return False


class WordPosSt(object):
    def __init__(self, db):
        self.__pos = []
        self.__worddb = db
        self.__load_entry_node()
        self.__load_alphabet()

    def __load_entry_node(self):
        self.entry_node = self.__worddb.get_entry_node_blob()

    def __load_alphabet(self):
        alphabet = self.__worddb.get_alphabet()
        self.a2i_dict = {}
        self.i2a_dict = {}
        for a, i in alphabet:
            self.a2i_dict[a] = i
            self.a2i_dict[i] = a

    def __create_entry_events(self, event):
        sl = self.entry_node['soft_links']
        for e in event:
            letter_id = self.a2i_dict[e.get_letter()]
            if not sl.has_key(letter_id):
                continue
            node_ids = sl[letter_id]['nodes']
            for n in node_ids:
                print n[1]
                wp = WordPos(None, 0, worddb.WordTreeItem(self.__worddb, n[1]))
                self.__pos.append(wp)

    def handle_event(self, event):
        next_pos = []
        self.__create_entry_events(event)
        for e in event:
            for wp in self.__pos:
                if wp.is_same(e):
                    wp.update_probability(e, event)  # Use complete event list to update children that intersects with this probability list
                elif wp.is_forkable(e):
                    wps_n = wp.fork(e)
                    print wps_n
                    for wp_n in wps_n:
                        wp_n.update_probability(e, event)
                    next_pos.extend(wps_n)

        self.__pos.extend(next_pos)
        for wp in self.__pos:
            wp.commit_probabilities()

        self.__kill_unrealible()

    def __kill_unrealible(self):
        pass
        # r_list = []
        # for wp in self.__pos:
        #     r_list.append(wp.eval_reliability())
        #
        # r_barrier = self.__eval_quantile_level(r_list, 0.9)
        # new_wp = []
        # for wp in self.__pos:
        #     if wp.eval_reliability() >= r_barrier:
        #         new_wp.append(wp)
        # self.__pos = new_wp


class NodePosObj(object):
    def __init__(self, tracker, parent, node):
        self.__tracker = tracker
        self.__parent = parent
        self.__node = node
        self.__subs = []

    def handle_event(self, event):
        pass

    def destroy(self):
        if self.__parent is None:
            return
        self.__parent.__remove_subnode(self)
        self.__tracker.remove_object(self)
        for s in self.__subs:
            s.__forget_parent()
            s.destroy()

    def __remove_subnode(self, np):
        self.__subs.remove(np)

    def __forget_parent(self):
        self.__parent = None

    def get_subnodes(self):
        return self.__subs


class NodePos(NodePosObj):
    def __init__(tracker, parent, node):
        NodePosObj.__init__(self, tracker, parent, node)

    def handle_event(self, event):
        for e in event:
            if self.is_same(e):
                pass
            elif self.is_accessible(e.get_letter()):
                if self.subnode_exists(e.get_letter()):
                    continue
                np = NodePos(self.tracker, self, self.__node.get_node_blob(e.get_letter())

class PosTracker2(object):
    def __init__(self, worddb):
        self.__worddb = worddb


class PosTracker(object):
    def __init__(self, worddb):
        self.worddb = worddb
        self.node_cache = {}
        self.__load_alphabet()
        self.__load_entry_node()
        self.active_nodes = {}
        self.__event_cnt = 0
        self.max_events = None
        self.wpst = WordPosSt(self.worddb)

    def __load_entry_node(self):
        self.entry_node = self.worddb.get_entry_node_blob()

    def __load_alphabet(self):
        alphabet = self.worddb.get_alphabet()
        self.a2i_dict = {}
        self.i2a_dict = {}
        for a, i in alphabet:
            self.a2i_dict[a] = i
            self.a2i_dict[i] = a

    def __get_dict_intersection(self, p1, p2):
        return [(p1_v, p2[k]) for k, p1_v in p1.items() if p2.has_key(k)]

    def __get_accessible_nodes(self, node, probabilities_dict):
        intersections = self.__get_dict_intersection(probabilities_dict, node["soft_links"])
        return [(probability, node_info["nodes"]) for probability, node_info in intersections]

    def __convert_probabilities_a2i(self, probabilities):
        p = {}
        for k, v in probabilities.items():
            p[self.a2i_dict[k]] = v
        return p

    def print_event(self, probabilities):
        event_info = u''
        for k, v in probabilities.items():
            event_info += k+u': '+str(v)+u', '
        print 'Event probabilities', event_info

    def add_event(self, events):
        self.wpst.handle_event(events)
        # print self.entry_node
        return
        prob_intersect = self.__get_dict_intersection(probabilities, self.entry_node["soft_links"])
        if None == self.max_events or self.max_events > self.__event_cnt:
            for p1_probability, ii in prob_intersect:
                accessible_nodes = ii["nodes"]
                for n in accessible_nodes:
                    self.event_step.goto_node(-1, n[1], n[2]*p1_probability)

        self.__event_cnt += 1

    def print_results(self):
        return
        probabilities_list = []
        self.event_step.switch_nodes(self.worddb)
        for node in self.event_step.get_original_nodes():
            if None == node.get_node_word():
                continue
            probabilities_list.append((node.get_probability(), node))
        probabilities_list.sort(pcmp)
        for p, node in probabilities_list:
            print node.get_node_id(), node.get_node_word(), p, p / (self.event_step.step_counter-node.initial_step), node.initial_step, self.event_step.step_counter
