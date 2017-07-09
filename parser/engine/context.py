from argparse import Namespace as ns


import parser.build.loader
import parser.engine.backlog
import parser.engine.events
import parser.engine.sequence


class MatcherContext(object):

    max_sparse_count = 1
    max_sequential_count = 0

    def __init__(self, matcher, event_listener, owner, offset=0):
        self._matcher = matcher
        self._event_listener = event_listener
        self.owner = owner
        self.__offset = offset
        self.sequences = []
        self.ctxs = []
        self.__blank = True
        self.__backlog = parser.engine.backlog.Backlog()
        self.__frozen = []
        self.__awaiting = []
        self.ctx_create()

    def empty(self):
        return len(self.sequences) == 0 and len(self.__awaiting) == 0

    def get_head(self):
        assert len(self.sequences) == 1
        head = self.sequences[0].get_head()
        return ns(
            form=head.get_form()
        )

    def get_heads(self):
        return [ns(form=sq.get_head().get_form()) for sq in self.sequences]

    def split_by_sequences(self):
        res = []
        print('split sequences sequences', self.sequences)
        for sq in self.sequences:
            m = MatcherContext(
                self._matcher,
                parser.engine.events.ContextEventsForwarder(
                    self._event_listener),
                self.owner,
                self.__offset
            )
            m.sequences = [sq, ]
            res.append(m)
        return res

    def get_sequences(self):
        return self.sequences

    def add_sequence(self, sq):
        self.sequences.append(sq)
        self.__blank = False

    def add_ctx(self, ctx):
        self.ctxs.append(ctx)

    def create_ctx(self, spec_name, event_listener=None, offset=0):
        matcher = self.owner.find_matcher(spec_name)
        mc = MatcherContext(matcher, event_listener, self, spec_name)
        self.ctxs.append(mc)
        return mc

    def checkout_sequences(self):
        sequences = self.sequences
        self.sequences = []
        return CheckedoutCtx(self, sequences)

    def checkout_contexts(self):
        ctxs = self.ctxs
        self.ctxs = []
        return CheckedoutCtxs(self, ctxs)

    def recursed_at_offset(self, ctx_name, offset):
        sparse_calls = 0
        sequential_calls = 0
        for se in self.__get_callstack():
            if se.offset < offset:
                return False
            if ctx_name == se.name:
                sparse_calls += 1
                sequential_calls += 1
                if sparse_calls > MatcherContext.max_sparse_count:
                    return True
                if sequential_calls > MatcherContext.max_sequential_count:
                    return True
                continue

            sequential_calls = 0

        return False

    def __get_callstack(self):
        o = self.owner
        while not isinstance(o, parser.build.loader.MatcherCallbacks):
            yield ns(
                name=o.get_name(),
                offset=o.get_offset()
            )
            o = o.owner

    def find_matcher(self, name):
        return self.owner.find_matcher(name)

    def add_wait(self, awaiting_sq):
        self.__awaiting.append(awaiting_sq)

    def del_wait(self, awaiting_sq):
        self.__awaiting.remove(awaiting_sq)

    def add_frozen(self, frozen_sq):
        self.__frozen.append(frozen_sq)

    def unfreeze_one(self):
        frozen = self.__frozen.pop()
        sq = frozen.pop_sequence()
        self.add_sequence(sq)
        if frozen:
            self.__frozen.append(frozen)

    def push_forms(self, forms):
        self.__backlog.push_head(forms)
        for ctx in self.ctxs:
            ctx.push_forms(forms)

    def push_sentence(self, sentence):
        for forms in sentence:
            self.push_forms(forms)

    def has_backlog(self):
        if self.__blank:
            return not self.__backlog.empty()
        for sq in self.sequences:
            if sq.has_backlog():
                return True
        return False

    def backlog(self):
        return self.__backlog

    def get_slave_backlog(self):
        return parser.engine.backlog.Backlog(self.__backlog)

    def run_until_complete(self):
        return self._matcher.match(self)

    def has_frozen(self):
        return len(self.__frozen) > 0

    def is_blank(self):
        return self.__blank

    def get_name(self):
        return self._matcher.get_name()

    def get_offset(self):
        return self.__offset

    def sequence_forked(self, sq, new_sq):
        self._event_listener.sequence_forked(self, sq, new_sq)

    def sequence_forking(self, sq):
        self._event_listener.sequence_forking(self, sq)

    def sequence_matched(self, sq):
        self.__backlog.forget_slave(sq.backlog())
        self._event_listener.sequence_matched(self, sq)

    def sequence_failed(self, sq):
        self.__backlog.forget_slave(sq.backlog())
        self._event_listener.sequence_failed(self, sq)

    def sequence_res(self, res):
        self._event_listener.sequence_res(self, res)

    def ctx_create(self):
        self._event_listener.ctx_create(self)

    def ctx_complete(self):
        self._event_listener.ctx_complete(self)


class Context(object):
    def __init__(self, int_ctx, event_listener):
        self.__int_ctx = int_ctx
        self.__event_listener = event_listener

    def intctx(self):
        return self.__int_ctx

    def push_sentence(self, s):
        self.__int_ctx.push_sentence(s)

    def attach(self, ctx):
        self.__event_listener.attach(ctx)

    def run_until_complete(self):
        self.__int_ctx.run_until_complete()


class CheckedoutCtx(object):
    def __init__(self, ctx, sequences):
        self.ctx = ctx
        self.__sequences = {id(sq): SupervisedSequence(
            sq=sq, checkedout=False, confirmed=False)
            for sq in sequences}

    def sequences(self):
        return [sq.sq for sq in self.__sequences.values()]

    def commit(self):
        for svsq in self.__sequences.values():
            assert not svsq.checkedout
            if isinstance(svsq.sq, parser.engine.sequence.UnfrozenSequence):
                continue
            if svsq.confirmed:
                self.ctx.add_sequence(svsq.sq)
            else:
                self.ctx.sequence_failed(svsq.sq)

    def checkout_sequence(self, sq):
        svsq = self.__sequences.get(id(sq), None)
        if svsq is not None:
            assert not svsq.checkedout
            svsq.checkedout = True
            return
        self.__sequences[id(sq)] = SupervisedSequence(sq, True, False)

    def confirm_sequence(self, sq):
        svsq = self.__sequences.get(id(sq), None)
        assert svsq is not None and svsq.checkedout
        svsq.checkedout = False
        svsq.confirmed = True

    def fail_sequence(self, sq):
        svsq = self.__sequences.pop(id(sq), None)
        assert svsq is not None and svsq.checkedout
        self.ctx.sequence_failed(sq)

    def ignore_sequence(self, sq):
        svsq = self.__sequences.get(id(sq), None)
        assert svsq is not None and svsq.checkedout
        svsq.checkedout = False
        svsq.confirmed = False

    def complete_sequence(self, sq):
        svsq = self.__sequences.pop(id(sq), None)
        assert svsq is not None and svsq.checkedout
        self.ctx.sequence_matched(sq)

    def freeze(self, frozen_sq):
        sq = frozen_sq.sq
        svsq = self.__sequences.pop(id(sq), None)
        assert svsq is not None and svsq.checkedout
        self.ctx.add_frozen(frozen_sq)

    def wait_sequence(self, sq):
        self.ctx.add_wait(sq)


class SupervisedSequence(object):
    def __init__(self, sq, checkedout, confirmed):
        self.sq = sq
        self.checkedout = checkedout
        self.confirmed = confirmed


class SupervisedContext(object):
    def __init__(self, ctx, checkedout):
        self.ctx = ctx
        self.checkedout = checkedout


class CheckedoutCtxs(object):
    def __init__(self, ctx, ctxs):
        self.ctx = ctx
        self.__ctxs = {id(c): SupervisedContext(ctx=c, checkedout=False)
                       for c in ctxs}

    def ctxs(self):
        return (c.ctx for c in self.__ctxs.values())

    def commit(self):
        for svctx in self.__ctxs.values():
            assert not svctx.checkedout
            self.ctx.add_ctx(svctx.ctx)

    def checkout(self, ctx):
        svctx = self.__ctxs.get(id(ctx), None)
        assert svctx is not None
        assert not svctx.checkedout
        svctx.checkedout = True

    def confirm(self, ctx):
        svsq = self.__ctxs.get(id(ctx), None)
        assert svsq is not None and svsq.checkedout
        svsq.checkedout = False

    def complete(self, ctx):
        svsq = self.__ctxs.pop(id(ctx), None)
        assert svsq is not None and svsq.checkedout
        svsq.ctx.ctx_complete()


def create_ctx(matcher, event_listener, owner=None):
    return MatcherContext(matcher, event_listener, owner)
