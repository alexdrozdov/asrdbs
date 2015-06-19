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
        letters = u"абвгдежзийклмнопрстуфхцчшщъьэюя"
        for l in letters:
            self.originals[l] = {}
        self.originals[u"а"][u"о"]=0.5
        self.originals[u"а"][u"у"]=0.5
        self.originals[u"а"][u"е"]=0.3
        self.originals[u"а"][u"и"]=0.3

        self.originals[u"о"][u"а"]=0.5
        self.originals[u"о"][u"у"]=0.5
        self.originals[u"о"][u"е"]=0.5
        self.originals[u"о"][u"и"]=0.5

        self.originals[u"у"][u"о"]=0.5
        self.originals[u"у"][u"а"]=0.3
        self.originals[u"у"][u"е"]=0.2
        self.originals[u"у"][u"и"]=0.5

        self.originals[u"е"][u"о"]=0.5
        self.originals[u"е"][u"у"]=0.2
        self.originals[u"е"][u"а"]=0.2
        self.originals[u"е"][u"и"]=0.5

        self.originals[u"и"][u"о"]=0.5
        self.originals[u"и"][u"у"]=0.5
        self.originals[u"и"][u"е"]=0.5
        self.originals[u"и"][u"а"]=0.3

        self.originals[u"б"][u"п"] = 0.4
        self.originals[u"п"][u"б"] = 0.4

        self.originals[u"с"][u"з"] = 0.5
        self.originals[u"з"][u"с"] = 0.5

        self.originals[u"в"][u"ф"] = 0.5
        self.originals[u"ф"][u"в"] = 0.5
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
            e = {l:randrange(0.8, 1.0)*p for l,p in replacements.items()}
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
        self.letters[u"а"] = LetterSimInfo(u"а", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters[u"о"] = LetterSimInfo(u"о", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters[u"у"] = LetterSimInfo(u"у", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters[u"е"] = LetterSimInfo(u"е", 4, None, back_intersection=0.3, forward_intersection=0.5)
        self.letters[u"и"] = LetterSimInfo(u"и", 4, None, back_intersection=0.3, forward_intersection=0.5)

        self.letters[u"м"] = LetterSimInfo(u"м", 4, None, back_intersection=0.3, forward_intersection=0.6)
        self.letters[u"н"] = LetterSimInfo(u"н", 4, None, back_intersection=0.3, forward_intersection=0.6)
        self.letters[u"л"] = LetterSimInfo(u"л", 4, None, back_intersection=0.3, forward_intersection=0.6)

        self.letters[u"в"] = LetterSimInfo(u"в", 4, None, back_intersection=0.0, forward_intersection=0.5)
        self.letters[u"г"] = LetterSimInfo(u"г", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"ж"] = LetterSimInfo(u"ж", 4, None, back_intersection=0.0, forward_intersection=0.5)
        self.letters[u"з"] = LetterSimInfo(u"з", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"р"] = LetterSimInfo(u"р", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"с"] = LetterSimInfo(u"с", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"ф"] = LetterSimInfo(u"ф", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"х"] = LetterSimInfo(u"х", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"ц"] = LetterSimInfo(u"ц", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"ч"] = LetterSimInfo(u"ч", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"ш"] = LetterSimInfo(u"ш", 4, None, back_intersection=0.0, forward_intersection=0.3)
        self.letters[u"щ"] = LetterSimInfo(u"щ", 4, None, back_intersection=0.0, forward_intersection=0.3 )

        self.letters[u"б"] = LetterSimInfo(u"б", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters[u"д"] = LetterSimInfo(u"д", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters[u"к"] = LetterSimInfo(u"к", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters[u"п"] = LetterSimInfo(u"п", 1, None, back_intersection=0.0, forward_intersection=0.0)
        self.letters[u"т"] = LetterSimInfo(u"т", 1, None, back_intersection=0.0, forward_intersection=0.0)

    def simulate(self, text, track_sequencer):
        self.active_letters = []
        for t in text:
            print "!!!!!!!!!!!!!!!!!Simulating", t
            if not self.letters.has_key(t):
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
        print step ,
        for l,p in probabilities.items():
            print l.encode("utf8"),":", round(p,3),", ",
        print ""
    def simulate_one_step(self, track_sequencer):
        active_letters = []
        probabilities = {}
        for a in self.active_letters:
            pr = a.get_probabilities(self.lrp)
            for l,p in pr.items():
                if probabilities.has_key(l) and probabilities[l]<p:
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
        print self.step_num ,
        for l,p in probabilities.items():
            print l.encode("utf8"),":", round(p,3),", ",
        print ""

if __name__=="__main__":
    ts = TextSimulator(LetterReplaceProbabilities())
    ts.simulate(u"влесуродиласьелочка", FakeTrackSequencer())

