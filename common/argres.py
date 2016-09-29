logs_enabled = False
argres_level = 0


def argres(show_result=True, repr_result=None):
    def argres_internal(func):
        "This decorator dumps out the arguments passed to a function before calling it"
        argnames = func.__code__.co_varnames[:func.__code__.co_argcount]
        fname = func.__name__

        def argres_fcn(*args, **kwargs):
            obj = args[0]
            logger = obj.get_logger()
            global argres_level
            argres_level += 1
            space = '  ' * argres_level
            if logger is not None:
                s = '>>{0}{1}: {2}'.format(space, fname, ', '.join(
                    '%s=%r' % entry
                    for entry in list(zip(argnames, args)) + list(kwargs.items())))
                logger.info(s)
            res = func(*args, **kwargs)
            if logger is not None and show_result:
                s = '<<{0}{1}: {2}'.format(space, fname, res if repr_result is None else repr_result(res))
                logger.info(s)
            argres_level -= 1
            return res

        if logs_enabled:
            return argres_fcn
        return func
    return argres_internal
