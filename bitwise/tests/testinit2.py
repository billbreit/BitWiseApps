
import os, sys


print()
print('=== In testinit2 -> os.getcwd ', os.getcwd())


print('import fsinit ?')
if __name__=='__main__':
    print('is running, import fsinit')
    if sys.implementation.name == 'micropython':
        os.chdir('/tests')
    import fsinit

print('testinit2 - import testinit1')

print('import tests.testinit1 as testinit1')
print()

try:
    import tests.testinit1 as testinit1
    print('import dev.testinit1 as testinit1: OK')
except:
    print("Error, trying import testinit1 " )
    import testinit1
    print('import testinit1: OK')


# import __init__  # weird but works in Py3.9



print()


print('dir(testinit1) ', dir(testinit1))
print()
testinit1.init111_fun()
print()

print('Moment of Truth ... wild import from ulib')
print()
print('sys.path ', sys.path )
print()

'''
if sys.implmentation.name=='micropython':
    save_dir = os.getcwd()
    os.chdir('/uli 
'''

try:
    import ulib.testimp1 as testimp1
    print('import ulib.testimp1 OK, Hip Hip Horray !!!')
except:
    import testimp1
    print('import testimp1 OK, Hip Hip Horray !!!')
    
if not testimp1:
    print('Try again tomorrow ... ')
    
print()

'''
print('testinit2 locals()')
ll      = locals().copy()
for k,v in ll.items():
        print(k, ' = ', v)
'''

print('Exiting testinit2')
