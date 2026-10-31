"""A Collection of Bit Logic Functions.

   Part of https://github.com/billbreit/BitWiseApps. """

import math



"""### Basic Bit Functions for Python versions and MicroPython ###

   The functions for bit_length and logar2 redefine Python behavior
   for the value 0.  In the ones-compliment world, 0 and 1 are coequal,
   where not(1)==False and not(0)==True, same information value.
   
   bitlength of 0 is 1 instead of 0, more like the bit info value.
   
   logar2 redefines python log( base=2 ): logar2(0) and logar2(1) are both 0.  In python
   log(0, 2) is a ValueError. 
   
   Note the underlying constraint: logar2 + 1 == bitlength.    

"""

def py_bitlength( bint: int ) -> int:
    """Builtin, very fast, since py3.1"""

    if bint < 0: return None  # error
    if bint == 0: return 1 # unlike python

    return bint.bit_length()

def py_logar2( bint:int ) -> int:
    """equivalent to floor(log2(x)) but faster, returns int not float."""

    if bint < 0: return None  # error
    if bint == 0: return 0   # rather than error

    return py_bitlength(bint) - 1

def py_bitcount( bint: int ) -> int:
    """py3.10+, Very fast"""

    if bint < 0: return None  # error

    return bint.bit_count()


"""MicroPython specific """

MPY_MAX_LOG2_POWER = 127
MPY_MAX_LOG2_VALUE = 2**127

def mpy_logar2(bint: int) -> int:
    """Replace log2 with int-powered function, avoids 2^127
       int->float meltdown on mpy, only works with ints."""

    if bint < 0: return None  # error
    if bint == 0: return 0   # rather than None ???
    log = 0

    while bint > MPY_MAX_LOG2_VALUE:
        log += MPY_MAX_LOG2_POWER
        bint >>= MPY_MAX_LOG2_POWER

    if bint > 0:
        log += math.floor(math.log2(bint))

    return log

def mpy_bitlength(bint: int) -> int:
    """solves problem math.log2(2**128, 2) -> infinity"""
    
    if bint < 0: return None  # error
    if bint == 0: return 1  # unlike Py bit_length()

    return mpy_logar2(bint) + 1
    
def mpy_bitcount(bint: int) -> int:
    """Count number of bits set in a binary integer.
       bin(x).count('1') also works, but very slow on mpy. """

    if bint < 0: return None  # error

    count = 0
    while bint > 0:
        bint &= bint - 1
        count += 1

    return count


try:  # Python
    (123).bit_length()
    py_bitlen_avail = True
    bit_length = py_bitlength
    logar2 = py_logar2
except AttributeError as e:    # micropython
    py_bitlen_avail = False
    bit_length = mpy_bitlength
    logar2 = mpy_logar2
    
try:
    (123).bit_count()
    py_bitcount_avail = True
    bit_count = py_bitcount    
except AttributeError as e:    # micropython or < py3.10
    py_bitcount_avail = False
    bit_count = mpy_bitcount
    
 
""" ### Basic Bit Manipulation Function ### """

def is_bitint( n: int ) -> bool:
    """Test for basic bitint type, a non-negative integer.  This is primarily
       a ones-complement interpretation for indexing into lists.
       Maybe size limit, bit_length < 500, starts getting seriously non-linear.
    """

    if not isinstance(n, int) or n < 0:
        return False

    return True
    
def power2(power: int) -> int:
    """Replace pow2 with faster power2 function, only works with ints."""

    if power < 0: return None  # error

    return 1 << power

def bit_indexes(bint: int) -> list[int]:
    """Make list of ints for indexes of bits that are set. Indexes are
       essentially the same as base-2 exponents.
       For example: bit_indexes(23) => [0, 1, 2, 4]
                    2^0 + 2^1 + 2^2 + 2^4 = 23
    """

    if bint < 0: return None  # error

    bit_idx = []
    while bint > 0:
        index = logar2(bint)
        bint &= (1 << index) - 1
        bit_idx.append(index)
    bit_idx.reverse()
        
    return bit_idx
    
def bit_from_indexes( indexes: list[int] ) -> int:
    """Make int for list of indexes,
    bit_from_indexes([0, 1, 2, 4])  => 23"""
    
    bint = 0
    for i in indexes:
        bint |= power2(i)
    return bint
    
def make_bitmask( length: int ) -> int:
    """Generate bit mask, make_bitmask(6) -> 0b111111"""
    
    return  (1 << length) - 1  

    
""" ### Basic Binary/Boolean Tests ### """

def one_bit_set(bint: int) -> bool:
    """Only one bit set in bint.
       alt -> if x!= 0: return 0 == (x & (x - 1)) """

    if not is_bitint(bint): return None

    if bint == 0:
        return False

    return 0 == (bint & (bint - 1))

def more_than_one_bit_set(bint: int) -> bool:
    """Only one bit set in bint.
       alt -> if x!= 0: return 0 == (x & (x - 1)) """

    if not is_bitint(bint): return None

    if bint == 0:
        return False

    return 0 != (bint & (bint - 1))
    
def one_of( x:int, y:int ) -> bool:
    """Only one of x in y. """
    if x == 0 or y ==0: return False
    t = bit_count(x & y)      # log2(x & y), faster  ?
    return t == 1             # floor(t)

def morethanone_of( x:int, y:int ) -> bool:
    """More than one of x in y. Detect conflict."""
    if x == 0 or y==0: return False
    t = bit_count(x & y)     # log2(x & y), faster ?
    return t > 1             # != floor(t)
    
def all_of( x:int, y:int ) -> bool:
    """All of x in y, equiv. to set.issubset.
      Note that all_of(x, y) != all_of(y,x) unless x==y.  """
    if x == 0: return False 
    return x & y == x

def any_of( x:int, y:int ) -> bool:
    """Any of integer x in y. """
    return x & y > 0

def none_of( x:int, y:int ) -> bool:
    """None of x in y."""
    return x & y == 0


"""Basic logical 'vector' operations on bit integers.
   Note that diff == diffTrue | diffFalse.   """

def diff( x:int, y:int ) -> int:
    """( 1, 0 ) or ( 0, 1 ), but not both nor neither ( XOR )"""
    return x ^ y
    
def diffTrue( old:int, new:int ) -> int:
    """Filter out evals that have gone from 1 -> 0.  Useful for ECA engine,
       condition eval as False will not trigger action, no need to test.
       In an inference engine, 0->1 might lead to an assertion."""
    return (old ^ new) & new 
    
def diffFalse( old:int, new:int ) -> int:
    """Filter out evals that have gone from 0 -> 1.  Useful for inference
       engine, condition 1->0 may lead to a retraction."""
    return (old ^ new) & old 

def match( x:int, y:int ) -> int:
    """Like all_of, but returns matched bits rather than bool.
    match(x, y) == 0 and not match(x, y) both work like none_of. """
    
    return x & y 

    

"""Bit Oerations, list-like capabilities for integer."""


def bit_get(bint: int, index: int) -> int:
    """Get bit n in bint x """

    if bint < 0: return None  # error

    return (bint >> index) & 1

def bit_set(bint: int, index: int ) -> int:
    """Set bit n in bint """

    if bint < 0: return None  # error

    return bint | (1 << index)

def bit_clear(bint:int, index:int ) -> int:
    """Clear bit n in bint """

    if bint < 0: return None  # error

    return bint & ~(1 << index)

def bit_toggle(bint: int, index: int) -> int:
    """Toggle bit, XOR """

    if bint < 0: return None   # error

    return bint ^ (1 << index)

def bit_remove(bint: int, index: int) -> int:
    """Remove bit at index."""

    if bint < 0: return None  # error
    if index < 0 or index > bit_length(bint)-1: return bint

    return (bint >> index+1) << index | bint & (1 << index)-1

def bit_insert(bint: int, index: int, value: int = 0) -> int:
    """insert bit value [0, 1] before index"""

    if value not in [0, 1] or bint < 0: return None  # error

    return (((bint >> index) << 1) | value) << index | bint & ((1 << index)-1)
    
    
""" Multi-bit/Bitslice operations, optimized, faster than theoretical limit,
    possilby due to int vectorization support."""

def bitslice_get(bint: int, index: int, bit_len: int) -> int:
    """Return bitlength bits at index."""  

    if bint < 0: return None  # error

    return (bint >> index) & ((1 << bit_len)-1)

def bitslice_set(bint: int, index: int, bit_len: int, value: int) -> int:
    """Overlay bitlength bits of value starting at index."""

    if bit_length(value) > bit_len or bint < 0: return None  # error

    return (((((bint >> (index+bit_len)) << bit_len) | value) << index) |
            (bint & (1 << index)-1))

def bitslice_insert(bint: int, index: int, bit_len: int, value: int) -> int:
    """Insert bitlength bits of value before index-th slot"""

    if bit_length(value) > bit_len or bint < 0: return None  # error

    return (((((bint >> index) << bit_len) | value) << index) |
            bint & ((1 << index) - 1))

def bitslice_remove(bint: int, index: int, bit_len: int) -> int:
    """Remove bitlength bits from index."""

    if bint < 0: return None
    if bint == 0: return 0

    return ((bint >> index + bit_len) << index) | bint & ((1 << index) - 1)


if __name__=='__main__':

    print('Quick Test')
    print()
    print('Python int.bit_length avail:', py_bitlen_avail)
    print('Python int.bit_count avail:', py_bitcount_avail)
    print()
    
    print('make_bitmask(i) for i in range(9)')
    for i in range(9):
        print(f'{i}   {make_bitmask(i):08b}')
    print()

    vals = [ 0, 1, 2, 3, 4, 12, 27, 30, 31, 44, 127, 128, 129, 255, 256, (2**20)-17 ]

    print('bit_length, , bit_count')
    print('-'*40)
    for x in vals:
        print( bin(x), ' = ', bit_length(x), bit_count(x))
    print()

    print('logar2, more like top_bit exp function than log, except for 0 !')
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
    


    
