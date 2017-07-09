class Backlog(object):
    def __init__(self, master=None):
        self.__master = master
        self.__slaves = []
        self.__entries = []
        if master is not None:
            master.attach_slave(self)

    def clone(self):
        bl = Backlog(self.__master)
        bl.__entries = [e for e in self.__entries]
        return bl

    def fetch_master(self):
        assert self.__master is not None
        assert not self.__entries
        assert len(self.__master.__slaves) == 1
        self.__entries = self.__master.__entries
        self.__master.__entries = []

    def attach_slave(self, slave):
        self.__slaves.append(slave)

    def forget_slave(self, slave):
        try:
            self.__slaves.remove(slave)
        except ValueError:
            pass

    def push_head(self, entry):
        if entry:
            if not self.__slaves:
                self.__entries.append(entry)
            else:
                for s in self.__slaves:
                    s.push_head(entry)

    def push_tail(self, entry):
        if self.__slaves:
            raise RuntimeError('Malicious pop push')
        self.__entries.insert(0, entry)

    def pop_tail(self):
        if self.__entries:
            return self.__entries.pop(0)
        raise RuntimeError('Backlog is empty')

    def get_tail(self):
        if self.__entries:
            return self.__entries[0]
        raise RuntimeError('Backlog is empty')

    def empty(self):
        if self.__entries:
            return False
        return True

    def __iter__(self):
        return iter(self.__entries)
