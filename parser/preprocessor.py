#!/usr/bin/env python
# -*- #coding: utf8 -*-


from argparse import Namespace as ns


class PreprocessorError(Exception):
    def __init__(self, stack, msg=None):
        self.__msg = '{0}: {1}'.format(stack.fmt_stack(), msg)

    def __str__(self):
        return '{0}'.format(self.__msg)


class PreprocessorContext(object):
    def __init__(self, name):
        self.__stack = [name, ]
        self.__dependencies = set()

    def push_stack(self, name):
        self.__stack.append(name)

    def pop_stack(self):
        d = self.__stack[-1]
        self.__stack = self.__stack[0:-1]
        return d

    def fmt_stack(self):
        return '/'.join(self.__stack)

    def add_dependency(self, name):
        self.__dependencies.add(name)

    def get_dependencies(self):
        return list(self.__dependencies)


class Preprocessor(object):
    def __init__(self):
        self.__supported_keys = {
            'id': self.__on_id,
            'repeatable': lambda (ctx, v): True,
            'include': self.__on_include,
            'master-slave': lambda (ctx, v): True,
            'add-to-seq': lambda (ctx, v): True,
            'required': lambda (ctx, v): True,
            'fsm': lambda (ctx, v): True,
            'entries': self.__on_entries,
            'anchor': lambda (ctx, v): True,
            'pos_type': lambda (ctx, v): True,
            'case': lambda (ctx, v): True,
            'reliability': lambda (ctx, v): True,
            'uniq-items': self.__on_uniq_items,
            'same-as': lambda (ctx, v): True,
            'merges-with': lambda (ctx, v): True,
            'dependency-off': lambda (ctx, v): True,
            'refers-to': lambda (ctx, v): True,
        }

    def __on_id(self, v):
        return True

    def __on_include(self, attrs):
        ctx, value = attrs
        if not isinstance(value, dict):
            raise PreprocessorError(
                ctx,
                'Include key expects value to be a dict, but got {0}'.format(
                    type(value)
                )
            )
        if not value.has_key('spec'):
            raise PreprocessorError(
                ctx,
                'Include dict requires at least "spec" key to be specified'
            )
        expected_keys = set(['spec', 'static-only', 'dynamic-only'])
        unexpected_keys = set(value.keys()) - expected_keys
        if unexpected_keys:
            raise PreprocessorError(
                ctx,
                'Include contains unexpected keys {0}'.format(
                    list(unexpected_keys)
                )
            )
        if not isinstance(value['spec'], str):
            raise PreprocessorError(
                ctx,
                'Include key value "spec" expects to be str, but got {0}'.format(
                    type(value['spec'])
                )
            )
        ctx.add_dependency(value['spec'])
        return True

    def __on_entries(self, attrs):
        ctx, value = attrs
        ctx.push_stack('entries')
        if not isinstance(value, list):
            raise PreprocessorError(ctx, 'List expected, but got {0}', type(value))
        self.__validate_list(ctx, value)
        ctx.pop_stack()
        return True

    def __on_uniq_items(self, attrs):
        ctx, value = attrs
        ctx.push_stack('uniq_items')
        if not isinstance(value, list):
            raise PreprocessorError(ctx, 'List expected, but got {0}', type(value))
        self.__validate_list(ctx, value)
        ctx.pop_stack()
        return True

    def __validate_list(self, ctx, l):
        for i, d in enumerate(l):
            ctx.push_stack('[{0}]'.format(i))
            if not isinstance(d, dict):
                raise PreprocessorError(ctx, 'Dict expected, but got {0}', type(d))
            self.__validate_dict(ctx, d)
            ctx.pop_stack()

    def __validate_dict(self, ctx, d):
        if not d.has_key('id'):
            raise PreprocessorError(ctx, "Required key 'id' is missing")

        ctx.push_stack(d['id'])
        for k, v in d.items():
            # ctx.push_stack(k)
            try:
                check_fcn = self.__supported_keys[k]
            except KeyError:
                raise PreprocessorError(ctx, "Unsupported key '{0}'".format(k))
            check_fcn((ctx, v))
        ctx.pop_stack()

    def __validate_spec(self, ctx, spec):
        if isinstance(spec, list):
            self.__validate_list(ctx, spec)
        elif isinstance(spec, dict):
            self.__validate_dict(ctx, spec)
        else:
            raise PreprocessorError(ctx, 'Unsupported entry type {0}', type(spec))

    def preprocess(self, spec):
        ctx = PreprocessorContext(spec.get_name())
        self.__validate_spec(ctx, spec.get_spec())
        return ns(
            dependencies=list(ctx.get_dependencies())
        )
