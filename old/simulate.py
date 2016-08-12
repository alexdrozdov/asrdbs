#!/usr/bin/env python
# -*- coding: utf-8 -*-

import simulate_words
import worddb
import trackers
import hypo

if __name__=="__main__":
    # twt = wordtree.TopWordTreeItem("o_dict.pickle", max_count=10000)
    # twt.store_complete_struct("dicttree.pickle")
    wdd = worddb.Worddb('./worddb1.db')
    # tseq = trackers.TrackSequencerEx(wdd)
    tseq = hypo.PosTracker(wdd)

    ts = simulate_words.TrivialTextSimulator()
    # ts = simulate_words.TextSimulator(simulate_words.LetterReplaceProbabilities())
    # ts.simulate(u"коробка", simulate_words.FakeTrackSequencer())
    # ts.simulate(u"таран", tseq)
    ts.simulate_events("таран", tseq)
    tseq.print_results()
