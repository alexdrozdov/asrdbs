import collections


class C3(object):
    @staticmethod
    def linearize(dependencies):
        res = {}
        dependencies = collections.defaultdict(list, dependencies)
        for head in list(dependencies):
            C3.__linearize(dependencies, head, res)
        return res

    @staticmethod
    def __findhead(sqs):
        for seq in sqs:
            if not any(seq[0] in s[1:] for s in sqs):
                return seq[0]
        raise ValueError("broken hierarchy")

    @staticmethod
    def __pophead(sqs, head):
        for seq in sqs:
            if seq[0] == head:
                seq = seq[1:]
            if seq:
                yield seq

    @staticmethod
    def __merge(sqs):
        sqs = [s for s in sqs if s]
        while sqs:
            head = C3.__findhead(sqs)
            sqs = list(C3.__pophead(sqs, head))
            yield head

    @staticmethod
    def __linearize(dependencies, head, results):
        if head in results:
            return results[head]
        res = list(C3.__merge(
            [[head]] +
            [C3.__linearize(
                dependencies, x, results
            ) for x in dependencies[head]] +
            ([dependencies[head]])
        ))
        results[head] = res
        return res


d = {
    '#object': ['#term'],
    '#edible': ['#term'],
    '#fruit': ['#object', '#edible'],
    '#apple': ['#fruit'],
}
print(C3.linearize(d))
