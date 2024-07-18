"""Condensed and optimized version of bitlogic.py in dev directory."""

import math

  

"""Platform independent functions """

def is_bitint( n:int ) -> bool:
    """Test for basic bitint type, a non-negative integer.
       This is primarily a ones-complement interpretation for indexing into lists.
       Maybe size limit, bit_length < 500, starts getting seriously non-linear.
    """

    if not isinstance( n, int) or n < 0:
        return False
        
    return True


def bit_indexes(bint:int) -> list:
    """Make list of ints for indexes of bits that are set. Indexes are
       essentially the same as base-2 exponents.
       For example: bitIndexes(23) => [0, 1, 2, 4]
                    2^0 + 2^1 + 2^2 + 2^4 = 23
    """

    if bint < 0: return None  # error
    
    bit_idx = []
    while bint > 0:
        index = logar2(bint)
        bint &= (1<<index) - 1
        bit_idx.insert(0, index)
    
    return bit_idx

def bit_count(bint:int) -> int:
    """Count number of bits set in a binary integer.
       bin(x).count('1') works for x >= 0. """
    
    if bint < 0: return None  # error

    count = 0
    while bint > 0:
        bint &= bint - 1
        count += 1
        
    return count


def power2(power:int) -> int:
    """Replace pow2 with faster power function, only works with ints."""

    if power < 0: return None  # error

    return 1 << power


"""Python specific"""
    
def py_bitlength( bint:int ) -> int:
    "Very fast"
    
    if bint < 0: return None  # error
    if bint == 0: return 1 # unlike python, may need to rethink this
    
    return bint.bit_length()

def py_logar2( bint:int ) -> int:
    """equivalent to floor(log2(x)) but faster"""
    
    if bint <= 0: return None  # error
    
    return py_bitlength(bint) - 1


"""MicroPython specific """


MPY_MAX_LOG2_POWER = 127
MPY_MAX_LOG2_VALUE = 2**127

def mpy_logar2(bint:int) -> int:
    """Replace log2 with int-powered function, avoids 2^127
       int->float meltdown on mpy, only works with ints."""
    
    
    if bint <= 0: return None  # error
    log = 0

    while bint > MPY_MAX_LOG2_VALUE:
        log += MPY_MAX_LOG2_POWER
        bint >>= MPY_MAX_LOG2_POWER
        
    if bint > 0:
        log += math.floor(math.log2(bint))
        
    return log

def mpy_bitlength( bint:int ) -> int:
    """solves problem math.log2(2**128, 2) -> infinity"""
   
    if bint == 0:
       return 1 # unlike Py bit_length()
       
    return mpy_logar2(bint) + 1


try:  # Python
    (123).bit_length()
    py_bitlen_avail = True
    bit_length = py_bitlength
    logar2 = py_logar2
except Exception as e:    # micropython
    py_bitlen_avail = False
    bit_length = mpy_bitlength
    logar2 = mpy_logar2
    
    
"""Bit and bitslice operations, list-like capabilities for integer."""

def bit_get( bint:int, index:int ) -> int:
    """Get bit n in integer x """
    
    if bint < 0: return None  # error
       
    return ( bint >> index ) & 1
    
def bit_set(bint:int, index:int ) -> int:
    """Set bit n in integer x """

    if bint < 0: return None  # error
        
    return bint | ( 1 << index)
    
def bit_clear(bint:int, index:int ) -> int:
    """Clear bit n in integer x """

    if bint < 0: return None  # error 
  
    return bint & ~( 1 << index )
    
def bit_toggle(bint:int, index:int) -> int:
    """Toggle bit, XOR """

    if bint < 0: return None   # error
        
    return bint ^ ( 1 << index)

def bit_remove(bint:int, index:int) -> int:

    if bint < 0: return None  # error
    if index < 0 or index > bit_length(bint)-1: return bint

    return (bint >> index+1 )<< index | bint&(1<<index)-1


def bit_insert(bint:int, index:int, value:int=0) -> int:
    """insert before index"""
    
    if value not in [0, 1] or bint < 0: return None  # error
    
    return (((bint >> index ) << 1 ) | value ) << index | bint&((1<<index)-1 )
   
    
def bitslice_get(bint:int, index:int, bit_len:int) -> int:

    if bint < 0: return None  # error
    
    return ( bint >> index ) & (( 1 << bit_len)-1)

    
def bitslice_set(bint:int, index:int, bit_len:int, value:int) -> int:
    """overlay"""
    
    if bit_length(value) > bit_len or bint < 0: return None  # error
    
    return (((( bint >> (index+bit_len)) << bit_len ) | value ) << index ) | ( bint & ( 1 << index)-1)

    
def bitslice_insert(bint:int, index:int, bit_len:int, value:int ) -> int:
    """Insert before index-th slot""" 

    if bit_length(value) > bit_len or bint < 0: return None  # error
    
    return (((( bint >> index ) << bit_len) | value ) << index ) | bint & (( 1 << index )-1)

    
def bitslice_remove(bint:int, index:int, bit_len:int) -> int:

    if bint < 0: return None
    if bint == 0: return 0
    
    return (( bint >> index+bit_len) << index ) | bint & (( 1 << index )-1)

    

if __name__=='__main__':
    
    print('Quick test')
    print()
    print('Python int.bit_length avail:', py_bitlen_avail) 
    
    vals = [ 0, 1, 2, 3, 4, 12, 27, 30, 31, 44, 127, 128, 129, 255, 256, (2**20)-17 ]
    
    print()    
    print('bit_length')
    print('-'*40)    
    for x in vals:
        print( bin(x), ' = ', bit_length(x) )
    print()
    
    print('logar2, more like top_bit exp function than log')
    print('-'*40)
        
    for x in vals:
        print( bin(x), ' = ', logar2(x))
    print()

    print('bit_indexes and bit_count')
    print('-'*40)
        
    for x in vals:
        print(f'{x:<8} , {x:>020b},  =  {bit_indexes(x)}   bit count = {bit_count(x)}')
    print()
    
    bi = bit_indexes(vals[-1])
    x = 0
    for b in bi:
        x |= power2(b)
        
    print('recovered val vals[-1] :', x)
    print('x == vals[-1]          :', x == vals[-1])
    

    
    
  
    
