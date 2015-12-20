def load_specdefs():
    global __all__
    import os
    import inspect
    import parser.speccmn
    local_path = os.path.dirname(os.path.realpath(__file__))
    __all__ = filter(
        lambda m: m != '__init__' and '.' not in m,
        set(
            map(
                lambda m: m.replace('.pyc', '.py').replace('.py', ''),
                os.listdir(local_path)
            )
        )
    )
    clss = []
    for mname in __all__:
        obj = __import__(mname, globals(), locals(), mname)
        clss.extend(
            map(
                lambda c: c[1],
                inspect.getmembers(
                    obj,
                    lambda c: inspect.isclass(c) and c is not parser.speccmn.SequenceSpec and issubclass(c, parser.speccmn.SequenceSpec)
                )
            )
        )
    return clss
