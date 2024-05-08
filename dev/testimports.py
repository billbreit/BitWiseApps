print('=== Testing Imports ===')
print()
try:
    import utils
    print('import utils worked')
    imp_utils_failed = False
except:
    print('import utils failed')
    imp_utils_failed = True
    
try:
    import dev.utils
    print('import dev.utils worked')
    imp_devutils_failed = False
except:
    print('import dev.utils failed')
    imp_devutils_failed = True
    


import os, sys

saved_path = sys.path[:]
print('path before ', saved_path)
print('pwd ', os.getcwd())

p = os.getcwd()

parentdir = ('/'.join(p.split('/')[:-1]))
print('parentdir ', parentdir)

if parentdir in sys.path:
    print('parentdir in sys.path')
    if parentdir+'/dev' in sys.path:
        print('parentdir/dev in sys.path')
    else:
        print('parentdir/dev not in sys.path ... appending.')        
        sys.path.append(parentdir + '/dev')
else:
    # print('parentdir not in sys.path, maybe alias')
    sys.path.append(parentdir)

print()
print('saved path ', saved_path)
print()
print('path after append', sys.path)
print()

if imp_utils_failed:
    import utils
if imp_devutils_failed:
    print(' ... trying import dev.utils again ...')
    try:
       import dev.utils
       print('It worked this time.')
    except:
        print('Failed again.')

