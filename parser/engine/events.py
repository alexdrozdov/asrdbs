class ContextEventHandler(object):
    def sequence_forked(self, ctx, sq, new_sq):
        pass

    def sequence_forking(self, ctx, sq):
        pass

    def sequence_matched(self, ctx, sq):
        pass

    def sequence_failed(self, ctx, sq):
        pass

    def sequence_res(self, ctx, res):
        pass

    def ctx_create(self, ctx):
        pass

    def ctx_complete(self, ctx):
        pass


class AwaitingEventListener(ContextEventHandler):
    def __init__(self, sq):
        self.__sq = sq

    def sequence_matched(self, ctx, sq):
        self.__sq.submatcher_matched(sq)

    def ctx_complete(self, ctx):
        self.__sq.subctx_complete(ctx)


class ContextOutputDispatcher(ContextEventHandler):
    def __init__(self):
        self.__attached = []

    def attach(self, ctx):
        self.__attached.append(ctx)

    def sequence_forked(self, ctx, sq, new_sq):
        for a in self.__attached:
            a.sequence_forked(ctx, sq, new_sq)

    def sequence_forking(self, ctx, sq):
        for a in self.__attached:
            a.sequence_forking(ctx, sq)

    def sequence_matched(self, ctx, sq):
        for a in self.__attached:
            a.sequence_matched(ctx, sq)

    def sequence_failed(self, ctx, sq):
        for a in self.__attached:
            a.sequence_failed(ctx, sq)

    def sequence_res(self, ctx, res):
        for a in self.__attached:
            a.sequence_res(ctx, res)

    def ctx_create(self, ctx):
        for a in self.__attached:
            a.ctx_create(ctx)

    def ctx_complete(self, ctx):
        for a in self.__attached:
            a.ctx_complete(ctx)


class ContextEventsForwarder(ContextEventHandler):
    def __init__(self, dst_listener):
        self.__dst = dst_listener

    def sequence_forked(self, ctx, sq, new_sq):
        self.__dst.sequence_forked(ctx, sq, new_sq)

    def sequence_forking(self, ctx, sq):
        self.__dst.sequence_forking(ctx, sq)

    def sequence_matched(self, ctx, sq):
        self.__dst.sequence_matched(ctx, sq)

    def sequence_failed(self, ctx, sq):
        self.__dst.sequence_failed(ctx, sq)

    def sequence_res(self, ctx, res):
        self.__dst.sequence_res(ctx, res)

    def ctx_create(self, ctx):
        self.__dst.ctx_create(ctx)

    def ctx_complete(self, ctx):
        self.__dst.ctx_complete(ctx)
