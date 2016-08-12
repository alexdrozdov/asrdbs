#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import copy


class Event(object):
    def __init__(self, letter, time, duration, probability):
        self.__letter = letter
        self.__time = time
        self.__duration = duration
        self.__probability = probability

    def begin(self):
        return self.__time

    def end(self):
        return self.__time + self.__duration

    def duration(self):
        return self.__duration

    def probability(self):
        return self.__probability

    def get_letter(self):
        return self.__letter


class LetterReplaceProbabilities:
    def __init__(self):
        self.originals={}
        letters = "абвгдежзийклмнопрстуфхцчшщъьэюя"
        for l in letters:
            self.originals[l] = {}
        self.originals["а"]["о"]=0.5
        self.originals["а"]["у"]=0.5
        self.originals["а"]["е"]=0.3
        self.originals["а"]["и"]=0.3

        self.originals["о"]["а"]=0.5
        self.originals["о"]["у"]=0.5
        self.originals["о"]["е"]=0.5
        self.originals["о"]["и"]=0.5

        self.originals["у"]["о"]=0.5
        self.originals["у"]["а"]=0.3
        self.originals["у"]["е"]=0.2
        self.originals["у"]["и"]=0.5

        self.originals["е"]["о"]=0.5
        self.originals["е"]["у"]=0.2
        self.originals["е"]["а"]=0.2
        self.originals["е"]["и"]=0.5

        self.originals["и"]["о"]=0.5
        self.originals["и"]["у"]=0.5
        self.originals["и"]["е"]=0.5
        self.originals["и"]["а"]=0.3

        self.originals["б"]["п"] = 0.4
        self.originals["п"]["б"] = 0.4

        self.originals["с"]["з"] = 0.5
        self.originals["з"]["с"] = 0.5

        self.originals["в"]["ф"] = 0.5
        self.originals["ф"]["в"] = 0.5
    def get_replacements(self,letter):
        try:
            return self.originals[letter]
        except:
            pass
        return None
    def get_probability(self, original, replacement):
        try:
            return self.originals[original][replacement]
        except:
            pass
        return 0.0

#Генератор случайных чисел. Да, отвратительный, зато обладает повторяемостью от запуска к запуску
#Ну и приложение отнюдь не знаимается криптографией
prev_rand=1
def rand():
    global prev_rand
    prev_rand = (73243*prev_rand+17)%65535
    return prev_rand
def randf():
    r = rand()/65535.0
    return r

def randrange(low, high):
    r=(high-low)*randf()+low
    return r


class LetterSimInfo:
    def __init__(self, letter, relative_length, replace_probabilities, back_intersection=0.0, forward_intersection=0.0):
        self.letter = letter
        self.relative_length = relative_length
        self.back_intersection = back_intersection
        self.forward_intersection = forward_intersection

class SimEntry:
    def __init__(self, letter_sim_info):
        self.letter_sim_info = letter_sim_info
        self.position = 0
    def get_probabilities(self, letter_replace_probabilities):
        letter = self.letter_sim_info.letter
        replacements = letter_replace_probabilities.get_replacements(letter)
        if None==replacements:
            e = {letter:1.0}
        else:
            e = {l:randrange(0.8, 1.0)*p for l,p in list(replacements.items())}
            e[letter] = randrange(0.7, 1.0)
        return e
    def step_forward(self):
        self.position += 1
        if self.position >= self.letter_sim_info.relative_length:
            return False
        return True
    def is_intersectible(self):
        intersectible_zone = self.letter_sim_info.relative_length*(1.0-self.letter_sim_info.forward_intersection)
        if self.position>=intersectible_zone:
            return True
        return False

class TextSimulator:
    def __init__(self, letter_replace_probabilies):
        self.position = 0
        self.letters = {}
        self.lrp = letter_replace_probabilies
        self.letters["а"] = LetterSimInfo("а", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters["о"] = LetterSimInfo("о", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters["у"] = LetterSimInfo("у", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters["е"] = LetterSimInfo("е", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters["и"] = LetterSimInfo("и", 4, None, back_intersection=0.3, forward_intersection=0.5)

        self.letters["м"] = LetterSimInfo("м", 4, None, back_intersection=0.3, forward_intersection=0.6)
        self.letters["н"] = LetterSimInfo("н", 4, None, back_intersection=0.3, forward_intersection=0.6)
        self.letters["л"] = LetterSimInfo("л", 4, None, back_intersection=0.3, forward_intersection=0.6)

        self.letters["в"] = LetterSimInfo("в", 4, None, back_intersection=0.0, forward_intersection=0.5)
        self.letters["г"] = LetterSimInfo("г", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["ж"] = LetterSimInfo("ж", 4, None, back_intersection=0.0, forward_intersection=0.5)
        self.letters["з"] = LetterSimInfo("з", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["р"] = LetterSimInfo("р", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["с"] = LetterSimInfo("с", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["ф"] = LetterSimInfo("ф", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["х"] = LetterSimInfo("х", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["ц"] = LetterSimInfo("ц", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["ч"] = LetterSimInfo("ч", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["ш"] = LetterSimInfo("ш", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters["щ"] = LetterSimInfo("щ", 4, None, back_intersection=0.0, forward_intersection=0.3 )

        self.letters["б"] = LetterSimInfo("б", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters["д"] = LetterSimInfo("д", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters["к"] = LetterSimInfo("к", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters["п"] = LetterSimInfo("п", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters["т"] = LetterSimInfo("т", 1, None, back_intersection=0.0, forward_intersection=0.0)

    def simulate(self, text, track_sequencer):
        self.active_letters = []
        for t in text:
            print("!!!!!!!!!!!!!!!!!Simulating", t)
            if t not in self.letters:
                continue
            lsi = self.letters[t]
            if lsi.back_intersection<0.01:
                self.finite_active_letters(track_sequencer) #Начало этого символа не может пересекаться с предыдущими - завершаем все предыдущие
                self.active_letters.append(SimEntry(lsi))
                self.simulate_one_step(track_sequencer)
                continue
            while not self.is_intersectible():
                self.simulate_one_step(track_sequencer)
            self.active_letters.append(SimEntry(lsi))
            self.simulate_one_step(track_sequencer)
        self.finite_active_letters(track_sequencer)
    def is_intersectible(self):
        for a in self.active_letters:
            if not a.is_intersectible():
                return False
        return True
    def finite_active_letters(self,track_sequencer):
        while len(self.active_letters)>0:
            self.simulate_one_step(track_sequencer)
    def print_step_probabilities(self, step, probabilities):
        print(step, end=' ')
        for l,p in list(probabilities.items()):
            print(l.encode("utf8"),":", round(p,3),", ", end=' ')
        print("")
    def simulate_one_step(self, track_sequencer):
        active_letters = []
        probabilities = {}
        for a in self.active_letters:
            pr = a.get_probabilities(self.lrp)
            for l,p in list(pr.items()):
                if l in probabilities and probabilities[l]<p:
                    probabilities[l] = p
                else:
                    probabilities[l] = p
            if a.step_forward():
                active_letters.append(a)
        self.active_letters = active_letters
        track_sequencer.add_event(probabilities)
        #self.print_step_probabilities(self.position, probabilities)
        self.position += 1

class TrivialTextSimulator(object):
    def __init__(self):
        pass
    def simulate(self, text, track_sequencer):
        for t in text:
            probabilities = {t:1.0}
            track_sequencer.add_event(probabilities)

    def simulate_events(self, text, track_sequencer):
        time = 0.0
        duration = 0.1
        for t in text:
            events = []
            e = Event(t, time, duration, 1.0)
            events.append(e)
            track_sequencer.add_event(events)
            time += duration


class FakeTrackSequencer:
    def __init__(self):
        self.step_num = 0
    def add_event(self, event):
        self.print_event_probabilities(event)
        self.step_num += 1
    def print_event_probabilities(self, probabilities):
        print(self.step_num, end=' ')
        for l,p in list(probabilities.items()):
            print(l.encode("utf8"),":", round(p,3),", ", end=' ')
        print("")

if __name__=="__main__":
    ts = TextSimulator(LetterReplaceProbabilities())
    ts.simulate("влесуродиласьелочка", FakeTrackSequencer())

