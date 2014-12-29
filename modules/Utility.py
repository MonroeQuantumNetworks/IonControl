from itertools import chain


def unique(seq):
    seen = set()
    return [ x for x in seq if x not in seen and not seen.add(x)]

def flatten(listOfLists):
    "Flatten one level of nesting"
    return chain.from_iterable(listOfLists)

def join( s, iterable ):
    """join ignoring None values"""
    return s.join( (i for i in iterable if i is not None and str(i) != ''))
