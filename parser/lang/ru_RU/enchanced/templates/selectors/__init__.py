#!/usr/bin/env python
# -*- #coding: utf8 -*-


def load_templates():
    global __all__
    import os
    import inspect
    import parser.templates.common
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
                    lambda c: inspect.isclass(c) and c is not parser.templates.common.SpecTemplate and issubclass(c, parser.templates.common.SpecTemplate)
                )
            )
        )
    return clss
