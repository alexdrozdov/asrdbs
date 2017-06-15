import parser.io.output
import parser.io.input


def input_sentence(ctx):
    return parser.io.input.SentenceInput(ctx)


def output_chain(ctx, *args):
    chain = [args[0](ctx), ]
    if 1 < len(args):
        other = args[1:]
        for o in other:
            chain.append(o(chain[-1]))
    return parser.io.output.OutputChainWrapper(chain[0], chain[-1])
