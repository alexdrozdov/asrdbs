import parser.spare
from parser.lang.base.rules.defs import RepeatableSpecs, WordSpecs


@parser.spare.at(name='phrases', namespace='specs')
@parser.spare.constructable
def phrases(phrases):
    r = []
    for i, p in enumerate(phrases):
        words = p.split()
        if len(words) == 1:
            r.append(
                {
                    "id": "$PARENT::phr-{0}".format(i),
                    "repeatable": RepeatableSpecs().Once(),
                    "pos_type": [WordSpecs().IsWord([words[0], ]), ],
                }
            )
            continue
        rr = []
        for j, w in enumerate(words):
            rr.append(
                {
                    "id": "$PARENT::phr-{0}_w-{1}".format(i, j),
                    "repeatable": RepeatableSpecs().Once(),
                    "pos_type": [WordSpecs().IsWord([w, ]), ],
                }
            )
        r.append(
            {
                "id": "$PARENT::phr-{0}".format(i),
                "repeatable": RepeatableSpecs().Once(),
                "entries": rr
            }
        )
    return r
