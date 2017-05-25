import parser.io.context


def input_sentence(ctx):
    return parser.io.context.SentenceInput(ctx)


def output_chain(ctx, *args):
    chain = [args[0](ctx), ]
    if 1 < len(args):
        other = args[1:]
        for o in other:
            chain.append(o(chain[-1]))
    return parser.io.context.OutputChainWrapper(chain[0], chain[-1])
