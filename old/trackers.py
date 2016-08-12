#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import traceback
import numpy


class NodeState(object):
    def __init__(self, node_id, probability = 0.0, initial_step = 0):
        self.node_id = node_id
        self.probability = probability
        self.node_json_info = {}
        self.initial_step = initial_step
    def get_node(self):
        return self.node_json_info
    def set_node(self, node_json_info):
        self.node_json_info = node_json_info
    def get_node_word(self):
        return self.node_json_info["word"]
    def get_node_id(self):
        return self.node_id
    def get_probability(self):
        return self.probability

class EventStep(object):
    def __init__(self, active_nodes = {}):
        self.original_nodes = {}
        self.next_step_nodes = {}
        self.step_counter = 0
    def __estimate_average_probability(self):
        return 0
        probabilities = [node.get_probability()/(self.step_counter-node.initial_step) for node in list(self.original_nodes.values())]
        probabilities.sort(reverse=True)
        p_len = len(probabilities)
        if p_len<50:
            return probabilities[-1]
        p_index = int(p_len*1.0)
        if p_index<50:
            return probabilities[p_index]
        return probabilities[50]
    def __remove_weak_nodes(self):
        if 0==len(self.original_nodes):
            return
        original_nodes = {}
        average_probability = self.__estimate_average_probability()
        for k,node in list(self.original_nodes.items()):
            if (self.step_counter-node.initial_step)>2 and node.get_probability()/(self.step_counter-node.initial_step)<average_probability:
                continue
            original_nodes[k] = node
        self.original_nodes = original_nodes
    def switch_nodes(self, worddb):
        self.step_counter += 1
        for node_state in list(self.next_step_nodes.values()):
            node_state.set_node(worddb.get_node_blob(node_state.get_node_id()))
            self.original_nodes[node_state.get_node_id()] = node_state
        self.next_step_nodes = {}
        self.__remove_weak_nodes()
    def get_original_nodes(self):
        return list(self.original_nodes.values())
    def print_event_step(self, msg=''):
        original_nodes = msg
        next_step_nodes = msg
        for k,v in list(self.original_nodes.items()):
            original_nodes += str(k)+': '+str(v.probability)+', '
        for k,v in list(self.next_step_nodes.items()):
            next_step_nodes += str(k)+': '+str(v.probability)+', '
    def goto_node(self, from_node, to_node, probability):
        #Проверяем, есть ли такой узел в оригинальной версии
        original_node_probability = 0.0
        initial_step = self.step_counter
        if from_node in self.original_nodes:
            original_node_probability = self.original_nodes[from_node].probability
            initial_step = self.original_nodes[from_node].initial_step
        ns_node_probability = original_node_probability + probability

        #Проверяем, добавляли ли мы такой узел в следующее поколение
        existed_ns_node_probability = 0.0
        if to_node in self.next_step_nodes:
            existed_ns_node_probability = self.next_step_nodes[to_node].probability #Определяем вероятность узла, которая уже существовала у нас ранее
            if ns_node_probability>existed_ns_node_probability:
                self.next_step_nodes[to_node].probability = ns_node_probability
        else:
            self.next_step_nodes[to_node] = NodeState(to_node, ns_node_probability, initial_step=initial_step)

def pcmp(l,r):
    if l[0]>r[0]:
        return -1
    if l[0]<r[0]:
        return 1
    return 0

class TrackSequencerEx:
    def __init__(self, worddb):
        self.worddb = worddb
        self.node_cache = {}
        self.__load_alphabet()
        self.__load_entry_node()
        self.active_nodes = {}
        self.__event_cnt = 0
        self.event_step = EventStep()
        self.max_events = None
    def __load_entry_node(self):
        self.entry_node = self.worddb.get_entry_node_blob()
    def __load_alphabet(self):
        alphabet = self.worddb.get_alphabet()
        self.a2i_dict = {}
        self.i2a_dict = {}
        for a,i in alphabet:
            self.a2i_dict[a] = i
            self.a2i_dict[i] = a
    def __get_dict_intersection(self, p1, p2):
        return [(p1_v,p2[k]) for k,p1_v in list(p1.items()) if k in p2]
    def __get_accessible_nodes(self, node, probabilities_dict):
        intersections = self.__get_dict_intersection(probabilities_dict, node["soft_links"])
        return [(probability, node_info["nodes"]) for probability,node_info in intersections ]
    def __convert_probabilities_a2i(self, probabilities):
        p = {}
        for k,v in list(probabilities.items()):
            p[self.a2i_dict[k]] = v
        return p
    def print_event(self, probabilities):
        event_info = ''
        for k,v in list(probabilities.items()):
            event_info += k+': '+str(v)+', '
        print('Event probabilities', event_info)
    def add_event(self, probabilities):
        self.event_step.switch_nodes(self.worddb)
        probabilities = self.__convert_probabilities_a2i(probabilities)
        #Обрабатывеем ранее встречавшиеся узлы
        for node_info in self.event_step.get_original_nodes():
            node = node_info.get_node()
            for p1_probability,accessible_nodes in self.__get_accessible_nodes(node, probabilities):
                for link_id, accessible_node_id,accessible_node_self_probability  in accessible_nodes:
                    self.event_step.goto_node(node_info.get_node_id(),
                                              accessible_node_id,
                                              accessible_node_self_probability*p1_probability)
        #Обрабатываем корневой узел
        prob_intersect = self.__get_dict_intersection(probabilities, self.entry_node["soft_links"])
        if None==self.max_events or self.max_events>self.__event_cnt:
            for p1_probability,ii in prob_intersect:
                accessible_nodes = ii["nodes"]
                for n in accessible_nodes:
                    self.event_step.goto_node(-1, n[1], n[2]*p1_probability)

        self.__event_cnt += 1
    def print_results(self):
        probabilities_list = []
        self.event_step.switch_nodes(self.worddb)
        for node in self.event_step.get_original_nodes():
            if None==node.get_node_word():
                continue
            probabilities_list.append((node.get_probability(), node))
        probabilities_list.sort(pcmp)
        for p, node in probabilities_list:
            print(node.get_node_id(), node.get_node_word(), p, p/(self.event_step.step_counter-node.initial_step), node.initial_step,self.event_step.step_counter)
