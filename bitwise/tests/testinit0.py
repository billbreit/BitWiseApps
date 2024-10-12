
import sys

print()
print('=== In testinit0 ')
print('If mpy testinit.py. gives locals but very sparse, no imports.')
print()

def test0000_fun():
	print('test0000 fun 111 !!!')

if sys.implementation.name == 'micropython':	
	print('In testinit0, locals() ->')
	ll	= locals().copy()
	for k,v in ll.items():
		print(k, ' = ', v)
print()

if __name__=='__main__':
    print('testinit0 not imported')
else:
    print('testinit0 imported')
    print("testinit0, locals()['__file__'] ", locals()['__file__'])
print()



