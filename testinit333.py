""" Extended test for initialization of Python and
    MicroPython environments ( fix sys.path ) """

import os, sys

print()
print('Starting testinit333 from ... ')
print()


print('Before init, os.getcwd() ->' , os.getcwd())
print()
print('Before init, sys.path -> ', sys.path)
print()

print('Importing init ...')
print()


import dev.init

# import dev.testinit2 # mpy no mod


print('After init, os.getcwd() ->' , os.getcwd())
print('After init, sys.path ->', sys.path)
print()

print('Trying import testinit2 ')

try:
    # import dev.testinit1 as testinit1
    import dev.testinit2 as testinit2
    print('import dev.testinit2 as testinit2: OK ')
except:
    # import testinit1
    import testinit2
    print('import testinit2 as testinit2: OK ')

print() 
print('Exiting testinit333')
