'''
Created on Feb 23, 2014

@author: pmaunz
'''

from modules import concatenate_iter
import unittest

class Concatenate_iter(unittest.TestCase):
    def testConcatenation(self):
        a = range(8)
        b = [8,9]
        c = (10,11,12)
        d = list(range(20))[13:20]
        concat = [ i for i in concatenate_iter.concatenate_iter(a,b,c,d)]
        self.assertEqual( concat, range(20))
        
    def testInterleaved(self):
        a = [1,4,7,10]
        b = (2,5,8)
        c = [3,6,9,'ignoreme']
        interleaved = [ i for i in concatenate_iter.interleave_iter(a,b,c)]
        self.assertEqual(interleaved, range(1,11))
        
if __name__ == "__main__":
    unittest.main()       