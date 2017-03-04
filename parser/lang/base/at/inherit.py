import copy
import parser.spare
from parser.lang.base.rules.defs import PosSpecs, RepeatableSpecs, AnchorSpecs, CaseSpecs


@parser.spare.at(name='inherit', namespace='specs')
class TemplateInherit(object):
    def __call__(self, body, *args, **kwargs):
        inh_list = body.popaslist('@inherit')
        rerun_required = False
        for base in inh_list:
            bb = self.__get_base(base)
            for k, v in list(bb.items()):
                rerun_required |= self.__extend_attr(body, k, v)
        if rerun_required:
            parser.spare.again()

    def __extend_attr(self, body, attr, val):
        body.setkey(attr, val)
        return attr.startswith('@')

    def __get_base(self, base):
        bases = {
            'basic-adj': {
                "pos_type": PosSpecs().IsAdjective()
            },
            'basic-adv': {
                "pos_type": PosSpecs().IsAdverb()
            },
            'basic-noun': {
                "pos_type": PosSpecs().IsNoun()
            },
            'preposition': {
                "pos_type": PosSpecs().IsPreposition()
            },
            'union': {
                "pos_type": PosSpecs().IsUnion()
            },
            'pronoun': {
                "pos_type": PosSpecs().IsPronoun()
            },
            'numeral': {
                "pos_type": PosSpecs().IsNumeral()
            },
            'comma': {
                "pos_type": PosSpecs().IsComma()
            },
            'once': {
                "repeatable": RepeatableSpecs().Once(),
            },
            'any': {
                "repeatable": RepeatableSpecs().Any(),
            },
            'once-or-none': {
                "repeatable": RepeatableSpecs().LessOrEqualThan(1),
            },
            'once-or-more': {
                "repeatable": RepeatableSpecs().EqualOrMoreThan(1),
            },
            'never': {
                "repeatable": RepeatableSpecs().Never(),
            },
            'anchor': {
                "anchor": AnchorSpecs().LocalSpecAnchor(),
            },
            '#object': {
                "@selector": "#object",
            },
            'genitive': {
                "case": CaseSpecs().IsCase(["genitive", ]),
            },
            'nominative': {
                "case": CaseSpecs().IsCase(["nominative", ]),
            },
            'soft-neg': {
                "@neg": {"strict": False},
            },
            'neg': {
                "@neg": {"strict": True},
            },
        }

        return copy.deepcopy(bases[base])
