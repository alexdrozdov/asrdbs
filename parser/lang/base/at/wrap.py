import parser.spare
from parser.lang.base.rules.defs import RepeatableSpecs, PosSpecs


@parser.spare.at(name='wrap', namespace='specs')
@parser.spare.constructable
def wrap(self, body, *args, **kwargs):
    wrap_info = body.pop('wrap')
    if before is None:
        before = [{
            "id": "$PARENT::comma-open",
            "repeatable": RepeatableSpecs().Once(),
            "pos_type": [PosSpecs().IsComma(), ],
            "merges-with": ["comma", ],
        }, ]
    if after is None:
        after = [{
            "id": "$PARENT::comma-close",
            "repeatable": RepeatableSpecs().Once(),
            "pos_type": [PosSpecs().IsComma(), ],
            "merges-with": ["comma", ],
        }, ]
    if isinstance(body, dict):
        body = [body, ]

    res = \
        {
            "id": entry_id,
            "repeatable": repeatable,
            "entries": before + body + after
        }
    if attrs is not None:
        res.update(attrs)
    return res
