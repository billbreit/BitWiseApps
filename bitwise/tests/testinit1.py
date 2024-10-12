

import os

print()
print('=== In tests.testinit1 -> os.getcwd ', os.getcwd())
print()

print('import init ?')
print()
if __name__=='__main__':
    print('is running as main, os.getcwd() ', os.getcwd())
    print()
    '''
    if os.getcwd() == '/':
        os.chdir('/dev')
        print('chdir() ', os.getcwd())
    print('init')
    '''
    print('Trying import init ')
    try:
        import test.fsinit # from /,
        print('import tests.init succeeded')
    except ImportError:
        import fsinit  # from subdir/,
        print('import init succeeded')  
print()
        


try:
    import tests.testinit0 as testinit0
    print('import tests.testinit0: OK')
except ImportError:
    import testinit0
    print('import testinit0: O')
except:
    print('import testinit0 failed')
    raise e
    

testinit0.test0000_fun()  # import failed ?'
print()

    
class ob(object):
    pass

def init111_fun():
    print('running init111_fun !!!')
    
obx = ob()

# init111_fun()

    
    
"""
print() 
print('testinit1 locals()')
ll  = locals().copy()
for k,v in ll.items():
    print(k, ' = ', v)
print()
"""


