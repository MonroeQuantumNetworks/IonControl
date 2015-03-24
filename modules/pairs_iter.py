'''
Created on Jan 17, 2015

@author: pmaunz
'''

def pairs_iter(lst):
    i = iter(lst)
    prev = item = i.next()
    for item in i:
        yield prev, item
        prev = item


if __name__=="__main__":
    for a,b in pairs_iter(range(10)):
        print a,b    
  