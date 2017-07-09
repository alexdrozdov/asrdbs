class NextSequenceStep(object):

    __slots__ = ('sq', 'valid', 'awaiting', 'frozen', 'transitions')

    def __init__(self, sq, valid, awaiting, frozen, transitions):
        self.sq = sq
        self.valid = valid
        self.awaiting = awaiting
        self.frozen = frozen
        self.transitions = transitions


class NextSequenceStepTransition(object):

    __slots__ = ('form', 'trs_def', 'fixed', 'probability')

    def __init__(self, form, trs_def, fixed, probability):
        self.form = form
        self.trs_def = trs_def
        self.fixed = fixed
        self.probability = probability


class TransitionAttempt(object):

    __slots__ = ('sq', 'trs')

    def __init__(self, sq, trs):
        self.sq = sq
        self.trs = trs


class TrsResult(object):

    __slots__ = ('sq', 'valid', 'fini', 'again', 'wait')

    def __init__(self, sq, valid, fini, again, wait):
        self.sq = sq
        self.valid = valid
        self.fini = fini
        self.again = again
        self.wait = wait
