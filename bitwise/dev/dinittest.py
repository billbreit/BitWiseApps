

import os, sys

print()
print('===== Testing dev.dinit FS init: dev.dinit.__init___ =====')
print()
print('In dev.dinit dir, os.getcwd ->', os.getcwd())
print()
print('In dev.dinit dir, sys.path  ->', sys.path)
print()
print(' ... importing dinit ...') 
import dinit
print()
print('dir(dinit) ', dir(dinit) )
print('... deleting ...')
del(dinit)
print()

print('Exiting dev.dinit dir, os.getcwd ->', os.getcwd())
print()
print('Existing dev.dinit dir, sys.path  ->', sys.path)
print()


