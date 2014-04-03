'''
Created on Apr 2, 2014

@author: pmaunz
'''




from modules.lru_cache import lru_cache
import time
import urllib
 

# @lru_cache
# def calculate( x ):
#     time.sleep(3)
#     return 2*x


# print calculate(1)
# print calculate(2)
# print calculate(1)
# print calculate(2)

class Peter:
    def __init__(self):
        self.peter = 17
        
    @lru_cache(maxsize=32)
    def fib(self, n):
        if n < 2:
            return n
        return self.fib(n-1) + self.fib(n-2)

p = Peter()
print [p.fib(n) for n in range(16)]

print p.fib.cache_info()
