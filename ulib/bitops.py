"""Condensed and optimized version of bitlogic.py in dev directory."""

import math

  

"""Platform independent functions """

def is_bitint( n:int ) -> bool:
    """Test for basic bitint type, a non-negative integer.
       This is primarily a ones-complement interpretation for indexing into lists.
       Maybe size limit, bit_length < 1000, starts getting seriously non-linear.
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

    if not is_bitint(bint):
        return None
    
    bit_idx = []
    while bint > 0:
        # index = floor(log2(bint))
        index = logar2(bint)
        bint &= power2(index) - 1
        bit_idx.insert(0, index)
    
    return bit_idx

def bit_count(bint:int) -> int:
    """Count number of bits set in a binary integer.
       bin(x).count('1') works for x >= 0. """
    
    if not is_bitint( bint):
        return None

    count = 0
    while bint > 0:
        bint &= bint - 1
        count += 1
        
    return count


def power2(power:int) -> int:
    """Replace pow2 with faster power function, only works with ints."""

    if not is_bitint(power):
        return None

    return 1 << power


"""Python specific"""
    
def py_bitlength( bint:int ) -> int:
    "Very fast"
    if bint == 0: return 1 # unlike python, may need to rethink this
    return bint.bit_length()

def py_logar2( bint:int ) -> int:
    """may be better to floor(log2(x)) ?"""
    if bint==0: return None
    return py_bitlength(bint) - 1


"""MicroPython specific """


MPY_MAX_LOG2_POWER = 127
MPY_MAX_LOG2_VALUE = 2**127

def mpy_logar2(bint:int) -> int:
    """Replace log2 with int-powered function, avoids 2^127
       int->float meltdown on mpy, only works with ints."""
    
    
    if bint == 0: return None
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


try:
    (123).bit_length()
    py_bitlen_avail = True
    bit_length = py_bitlength
    logar2 = py_logar2
except Exception as e:
    py_bitlen_avail = False
    bit_length = mpy_bitlength
    logar2 = mpy_logar2

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
        print( bin(x), ' = ', bit_indexes(x), ' bit count = ', bit_count(x))
    print()
    
    bi = bit_indexes(vals[-1])
    
    x = 0
    for b in bi:
        x |= power2(b)
        
    print('recovered val vals[-1] :', x)
    print('x == vals[-1]          :', x == vals[-1])
    
    
  
    
