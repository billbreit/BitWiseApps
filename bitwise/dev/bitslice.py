
"""Bit integer manipulation, single bit and list-like slicing functions."""

# from math import floor, log

try:
	from bitlogic import bit_length
except:
	from dev.bitlogic import bit_length
	

	


def bit_get( bint:int, n:int ):
	"""Get bit n in integer x """
	   
	return ( bint >> n ) & 1
	
def bit_set(bint:int, index:int, value:int=1 ):
	"""Set bit n in integer x """
	
	return (((bint >> index+1 ) << 1 ) | value ) << index | bint&((1<<index)-1 )
	
def bit_clear(bint:int, n:int ):
	"""Clear bit n in integer x """
  
	return bint & ~( 1 << n )
	
def bit_toggle(bint:int, n:int):
	"""Toggle bit, XOR """
		
	return bint ^ ( 1 << n)


def bit_remove(bint, index):

	if bint <= 0: return 0
	if index < 0 or index > bit_length(bint)-1: return bint
	
	print(bint, bin(bint), index)
	print('right shift + 1 then left shift ', bin((bint >> index +1 ) << index ))
	print('remainder  ', bin(bint&(1<<index)))
	x = (bint >> index+1 )<< index | bint&(1<<index)-1
	return x

def bit_insert(bint, index, value=0):
	"""insert before index"""
	
	if value not in [0, 1]: return None  # error
	
	print('bint, index, value ', bint, index, value)
	print('shiftright + left ', bin((bint >> index )<<1))
	print('remainder ', bin(bint&((1<<index)-1)))
	x = (((bint >> index ) << 1 ) | value ) << index | bint&((1<<index)-1 )

	# if value == 1: x = x | pow(2, index) 
	return x
	
	
def bitslice_get(bint, index, bit_len):

	print('bint, index, bit_length ', bint, index, bit_len )
	print('shiftright ', bin((bint >> index )))
	print('bit_len mask ', bin(( 1 << bit_len )-1 ))
	
	x = ( bint >> index ) & (( 1 << bit_len)-1)
	
	return x
	
def bitslice_set(bint, index, bit_len, value):
	"""overlay"""
	
	if bit_length(value) > bit_len: return None # error

	print('bint, index, bit_length, value ', bint, index, bit_len, value )
	print('shiftright then left bitlen ', bin((( bint >> index ) << bit_len )))
	print('remainder ', bin(( bint & ( 1 << index)-1)))
	
	x = (((( bint >> (index+bit_len)) << bit_len ) | value ) << index ) | ( bint & ( 1 << index)-1)
	
	return x
	
def bitslice_insert(bint, index, bit_len, value ):
	"""Insert before index-th slot""" 

	if bit_length(value) > bit_len: return None # error

	print('bint, index, bit_length, value ', bint, index, bit_len, value )
	print('shiftright then left ', bin(((( bint >> index ) << bit_len ))))
	print('remainder ', bin( bint & ( 1 << index )-1))
	
	x = (((( bint >> index ) << bit_len) | value ) << index ) | bint & (( 1 << index )-1)
	
	return x
	
def bitslice_remove(bint, index, bit_len):

	if bint == 0: return 0

	print('bint, index, bit_length ', bint, index, bit_len )
	print('shiftright then left ', bin(( bint >> index+bit_len) << index ))
	print('remainder ', bin( bint & ( 1 << index )-1))
	
	x = (( bint >> index+bit_len) << index ) | bint & (( 1 << index )-1)
	
	return x
	
	
if __name__ == "__main__":



	
	"""
	print('Testing bit_remove')
	print()

	for i in [ 0, 1, 5, 7, 8, 11, 17, 21 ]:
		print()
		for j in [ -1, 0, 1, 2, 3, 7 ]:
			x = bit_remove(i, j)
			print('bit_remove: ', i, bin(i), 'index ', j, 'returned ', bin(x) )
			print()
			
	"""
	
	"""

	print()
	print('Testing bit_insert')
	print()

	for i in [ 0, 1, 5, 7, 8, 11, 14, 21 ]:

		for j in [ 0, 1, 2, 6 ]:
			x = bit_insert(i, j, 1)
			print('bit_insert: int ', bin(i), 'index ', j, 'value 1 returned ', bin(x ))
			print()
			
	print('bit_insert: test value to insert not in [0, 1], Return should be None -> ', bit_insert(33, 3, 3))
	print()

	"""
	
	"""

			
	print()
	print('Testing bitslice_get')
	print()


	for n in [ 10, 85, 52428 ]:  # int
		for i in [ 0, 1, 3, 6 ]:  # index
			for k in [ 1, 4, 5 ]:  # bit length, eliminate 0, always 0
				x = bitslice_get(n, i, k)
				print('bitslice_get: int ', bin(n), 'index ', i, 'length ', k, 'returned ',bin(x) )
				print()
 
	
	"""
	
	"""

	print()
	print('Testing bitslice_set')
	print()


	for n in [ 0, 85, 52428 ]:  # int
		for i in [ 0, 3, 6, 11 ]:  # index
			for k in [ 1, 2, 5 ]:  # bit length, eliminate 0, always 0
				mask = (1<<k)-1
				x = bitslice_set(n, i, k, mask)
				r = 'None' if x is None else bin(x) 
				print('bitslice_set: int ', bin(n), 'index ', i, 'length ', k, 'value ', bin(mask),  'returned ', r )
				print()
				
	print('bitslice_set: bit_length(value to insert ) > bit_len to insert. Return should be None. ->', bitslice_set(33, 3, 2, 4))
	print()

	"""
	
	"""            
	print()
	print('Testing bitslice_insert')
	print()


	for n in [ 0, 85, 29127, 52428 ]:  # int
		for i in [ 0, 3, 6, 11 ]:  # index
			for k in [ 1, 2, 5 ]:  # bit length, eliminate 0, always 0
				mask = (1<<k)-1
				x = bitslice_insert(n, i, k, mask)
				print('bit slice_insert: int ', bin(n), 'index ', i,  'length ', k, 'value ', bin(mask), 'returned ',bin(x) )
				print()
				
	print('bitslice_insert: bit_length(value to insert ) > bit_len to insert. Return should be None. ->', bitslice_insert(33, 3, 2, 4))
	print()
	
	"""

	#""
	print()
	print('Testing bitslice_remove')
	print()



	for n in [ 1, 44, 85, 52428 ]:  # int
		for i in [ 0, 3, 6, 11 ]:  # index
			for k in [ 1, 2, 5, 6 ]:  # bit length, eliminate 0, always 0
				x = bitslice_remove(n, i, k)
				print('bitslice_remove: int ', bin(n), 'index ', i,  'length ', k,  'returned ',bin(x) )
				print()
   # """
