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
            'repeatable': lambda ctx_v: True,
            'include': self.__on_include,
            'master-slave': lambda ctx_v1: True,
            'add-to-seq': lambda ctx_v2: True,
            'required': lambda ctx_v3: True,
            'fsm': lambda ctx_v4: True,
            'entries': self.__on_entries,
            'anchor': lambda ctx_v5: True,
            'pos_type': lambda ctx_v6: True,
            'case': lambda ctx_v7: True,
            'reliability': lambda ctx_v8: True,
            'uniq-items': self.__on_uniq_items,
            'same-as': lambda ctx_v9: True,
            'merges-with': lambda ctx_v10: True,
            'dependency-of': lambda ctx_v11: True,
            'refers-to': lambda ctx_v12: True,
            'virtual': lambda ctx_v13: True,
            'form-info': lambda ctx_v14: True,
            'uniq': lambda ctx_v15: True,
            'action': lambda ctx_v16: True,
            'closed-with': lambda ctx_v17: True,
            'closed': lambda ctx_v18: True,
            'exclusive-with': lambda ctx_v19: True,
            'selector': lambda ctx_v20: True,
            'do-not-compile': lambda ctx_v21: True,
            'sibling': self.__on_sibling,
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
        if 'spec' not in value:
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

    def __on_sibling(self, attrs):
        ctx, value = attrs
        if not isinstance(value, dict):
            raise PreprocessorError(
                ctx,
                'Siblings key expects value to be a dict, but got {0}'.format(
                    type(value)
                )
            )
        expected_keys = set(['specs', 'role'])
        unexpected_keys = set(value.keys()) - expected_keys
        if unexpected_keys:
            raise PreprocessorError(
                ctx,
                'Siblings contains unexpected keys {0}'.format(
                    list(unexpected_keys)
                )
            )
        if 'specs' in value:
            for spec in value['specs']:
                ctx.add_dependency(spec)
        return True

    def __on_entries(self, attrs):
        ctx, value = attrs
        ctx.push_stack('entries')
        if not isinstance(value, list):
            raise PreprocessorError(
                ctx, 'List expected, but got {0}'.format(type(value)))
        self.__validate_list(ctx, value)
        ctx.pop_stack()
        return True

    def __on_uniq_items(self, attrs):
        ctx, value = attrs
        ctx.push_stack('uniq_items')
        if not isinstance(value, list):
            raise PreprocessorError(
                ctx, 'List expected, but got {0}'.format(type(value)))
        self.__validate_list(ctx, value)
        ctx.pop_stack()
        return True

    def __validate_list(self, ctx, l):
        for i, d in enumerate(l):
            ctx.push_stack('[{0}]'.format(i))
            if not isinstance(d, dict):
                raise PreprocessorError(
                    ctx, 'Dict expected, but got {0}'.format(type(d)))
            self.__validate_dict(ctx, d)
            ctx.pop_stack()

    def __validate_dict(self, ctx, d):
        if 'id' not in d:
            raise PreprocessorError(ctx, "Required key 'id' is missing")
        if 'repeatable' not in d and 'required' not in d:
            print(d)
            raise PreprocessorError(
                ctx,
                "Required key 'repeatable' or 'required' are missing"
            )

        ctx.push_stack(d['id'])
        for k, v in list(d.items()):
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
