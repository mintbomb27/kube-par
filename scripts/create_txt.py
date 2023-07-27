import os
import random

lines = 1000000
l = 0

f = open('input.txt','w+')
while l <= lines:
    f.write(str(random.randint(1,10**random.randint(0,10)))+'\n')
    l+=1
