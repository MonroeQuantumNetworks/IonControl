# -*- coding: utf-8 -*-
"""
Created on Thu Jan 03 07:11:22 2013

enum like class in python
see stackoverflow

@author: plmaunz
"""

from collections import OrderedDict


def enum(*sequential, **named):
    enums = OrderedDict(zip(sequential, range(len(sequential))), **named)
    reverse, forward = dict((value, key) for key, value in enums.iteritems()), enums.copy()
    enums['reverse_mapping'] = reverse
    enums['mapping'] = forward
    return type('Enum', (), enums)
    
if __name__ == "__main__":
    Numbers = enum('ZERO', 'ONE', 'TWO')
    state = Numbers.ZERO
    print state
    print state == 0
    state = 1
    print state == Numbers.ONE
    print Numbers.mapping['ZERO']
    print Numbers.reverse_mapping[2]
    print Numbers.mapping.keys()
    print Numbers.mapping
