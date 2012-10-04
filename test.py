import numpy as np



class C(object):
    def __init__(self):
        self.cat = 3

    def printCat(self):
        print self.cat

class B(C):
    def __init__(self):
        super(B,self).__init__()
        self.bat = 2

    def printBat(self):
        print self.bat

class A(B):
    def __init__(self):
        super(A,self).__init__()
        self.ant = 1
    
    def printAnt(self):
        print self.ant



blah = A()
blah.printAnt()
blah.printBat()
blah.printCat()

