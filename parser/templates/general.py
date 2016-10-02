import parser.spare
from parser.lang.sdefs import PosSpecs, WordSpecs, RelationsSpecs, CaseSpecs


@parser.spare.at(name='pos', namespace='selectors')
@parser.spare.constructable
def at_pos(body, *args, **kwargs):
    names = body.pop('@pos')
    if not isinstance(names, list):
        names = [names, ]
    body['pos'] = [PosSpecs().IsPos(names), ]


@parser.spare.at(name='word', namespace='selectors')
@parser.spare.constructable
def word(body, *args, **kwargs):
    words = body.pop('@word')
    if not isinstance(words, list):
        words = [words, ]
    body['word'] = [WordSpecs().IsWord(words), ]


@parser.spare.at(name='case', namespace='selectors')
@parser.spare.constructable
def case(body, *args, **kwargs):
    cases = body.pop('@case')
    if not isinstance(cases, list):
        cases = [cases, ]
    body['case'] = [CaseSpecs().IsCase(cases), ]


@parser.spare.at(name='animation', namespace='selectors')
@parser.spare.constructable
def animation(body, *args, **kwargs):
    qualifier = str(body.pop('@animation'))
    inv = qualifier.startswith('!') or qualifier.startswith('in')
    if inv:
        qualifier = qualifier.replace('!', '').replace('in', '')
    assert qualifier == 'animated'
    body['animation'] = [PosSpecs().IsAnimated() if not inv else PosSpecs().IsInanimated(), ]


@parser.spare.at(name='self', namespace='selectors')
@parser.spare.constructable
def at_self(body, *args, **kwargs):
    body['0'] = body.pop('@self')


@parser.spare.at(name='other', namespace='selectors')
@parser.spare.constructable
def other(body, *args, **kwargs):
    body['1'] = body.pop('@other')


@parser.spare.at(name='equal-properties', namespace='selectors')
@parser.spare.constructable
def equal_properties(body, *args, **kwargs):
    ep = body.pop('@equal-properties')
    body['equal-properties'] = [RelationsSpecs().EqualProps(int(other_indx_s[0]), other_indx_s[1]) for other_indx_s in list(ep.items())]


@parser.spare.at(name='position', namespace='selectors')
@parser.spare.constructable
def position(body, *args, **kwargs):
    pr = body.pop('@position')
    body['position'] = [RelationsSpecs().Position(int(other_indx_s1[0]), other_indx_s1[1]) for other_indx_s1 in list(pr.items())]


@parser.spare.at(name='link', namespace='selectors')
@parser.spare.constructable
def link(body, *args, **kwargs):
    body['link'] = body.pop('@link')
