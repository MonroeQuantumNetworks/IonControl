'''
Created on Feb 23, 2014

@author: pmaunz
'''

from modules import bidict
import unittest

class BidictTest(unittest.TestCase):
    def testNamedBiDict(self):
        Phonebook = bidict.namedbidict('Phonebook', 'number', 'name')
        phonebook = Phonebook()
        phonebook.number['Peter'] = '734-236-1042'
        self.assertEqual(phonebook.name['734-236-1042'], 'Peter' )

if __name__ == "__main__":
    unittest.main() 