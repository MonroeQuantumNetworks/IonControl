# -*- coding: utf-8 -*-
"""
Created on Thu Jan 03 07:11:22 2013

@author: plmaunz
"""

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)
    
if __name__ == "__main__":
    Numbers = enum('ZERO', 'ONE', 'TWO')
    state = Numbers.ZERO
    print state
    print Numbers.reverse_mapping[(state+1)%len(enums)]
