
"""

Common logic functions for binary integer logic.

Be aware that there are a few ones-complement interpretations of bit integers,
such as bit_length of '0' is 1, not the standard python 0.

Logic inversion ( the ~ function ) should only be used inside of expressions.
Inverses like ~0b1101 produce -0b1110, not 0b0010, and are useless
for indexing into a list unless used in a strictly twos-complement context,
like a & ~b. 

Runs on Python 3.9 and micropython v1.20.0 on a Pico.

module:     bitlogic
version:    v0.3.3
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2023 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer
    
"""

import os, sys
p = os.getcwd()
parentdir = ('/'.join(p.split('/')[:-1]))
sys.path.append(parentdir)

from math import log2, floor, ceil
from random import randint, choice
from lib.functools import partial


class BitLogicException(Exception):
    pass

    
def genrandint(size):
    """ Overcome 2**30 barrier in mpy, size is base 2 exponent.  Numbers are probably
        more arbitrary than random. Use for performance testing only."""
   
    MAX_2EXP = 30
    MAX_VALUE = 2**MAX_2EXP
    
    dvd, man = divmod(size, MAX_2EXP)
    rint = 0
 
    for d in range(dvd):
        rint|= rint << MAX_2EXP | randint(0, MAX_VALUE)
        
    if man > 0:
        rint|= rint << man | randint(0, 2**man)
        
    return rint  


nl = print
DEBUG = False



def is_bitint( n:int ):
    """Test for basic bitint type, a non-negative integer.
       This is primarily a ones-complement interpretation for indexing into lists.
       Maybe size limit, bit_length < 1000, starts getting non-linear.
    """

    if not isinstance( n, int) or n < 0:
        return False
        
    return True




""" Functions """

def power2(power:int) -> int:
    """Replace pow2 with faster power function, only works with ints."""

    if not is_bitint(power):
        return None

    return 1 << power
    
def logar2(bint:int) -> int:
    """Replace log2 with int-powered function, only works with ints.""" 
    
    if not is_bitint( bint) or bint == 0:  # log2(0) -> math domain error
        return None
    
    return bit_length_alt(bint) - 1

# Bit Level Functions

def bit_get( bint:int, n:int ):
    """Get bit n in integer x """
    
    if not is_bitint(bint):
        return None
        
    return ( bint >> n ) & 1
    
def bit_set(bint:int, n:int ):
    """Set bit n in integer x """
    
    if not is_bitint(bint):
        return None
        
    return bint | power2(n)
    
def bit_clear(bint:int, n:int ):
    """Clear bit n in integer x """
    
    if not is_bitint(bint):
        return None
        
    return bint & ~power2(n)
    
def bit_toggle(bint:int, n:int):

    if not is_bitint(bint):
        return None
        
    return bint ^ power2(n)


""" Bit Delpletion Functions
    Excellent for large sparse bitints, i.e. for indexing into lists.
    Number of loops is number of bits set, not bit length """

def bit_count(bint:int):
    """Count number of bits set in a binary integer.
       bin(x).count('1') works for x >= 0. """
    
    if not is_bitint( bint):
        return None

    count = 0
    while bint > 0:
        bint &= bint - 1
        count += 1
        
    return count

def bit_indexes(bint:int):
    """Make list of ints for indexes of bits that are set. Indexes are
       essentially the same as base-2 exponents.
       For example: bitIndexes(23) => [0, 1, 2, 4]
                    2^0 + 2^1 + 2^2 + 2^4 = 23
    """
    
    # print('bint xxxxxxxxxxxx ', bint), inf > 2**127

    if not is_bitint(bint):
        return None
    
    bit_idx = []
    while bint > 0:
        # index = floor(log2(bint))
        index = logar2(bint)
        bint &= power2(index) - 1
        bit_idx.insert(0, index)
    
    return bit_idx

def one_bit_set(bint:int):
    """Only one bit set in bint. 
       alt -> if x!= 0: return 0 == (x & (x - 1)) """
    
    if not is_bitint(bint):
        return None
        
    if bint == 0: return False
        
    return 0 == ( bint & (bint - 1))
    
def more_than_one_bit_set(bint:int):
    """Only one bit set in bint. 
       alt -> if x!= 0: return 0 == (x & (x - 1)) """
    
    if not is_bitint(bint):
        return None
        
    if bint == 0: return False
        
    return 0 != ( bint & (bint - 1))
    
def bit_length_alt(bint:int):
    """Position of highest non-zero bit""" 
    
    if not is_bitint(bint):
      return 0
            
    if bint == 0:
       return 1 # unlike Py bit_length()
    
    blen = 0
    while bint > 0:
        bint >>= 1
        blen += 1
    return blen
    
    
def bit_length_chunk(bint:int, chunk_size:int = 3):
    """like above with chunking, chunk_size=3 from T&E, 30% faster at 2^300"""
    
    if not is_bitint(bint):
      return 0
            
    if bint == 0:
       return 1 # unlike Py bit_length()
    
    blen = 0
    chunk = 2**chunk_size
    
    while bint > chunk:
        bint >>= chunk_size
        blen += chunk_size
        
    while bint > 0:
        bint >>= 1
        blen += 1
        
    return blen    
    

def bit_length( bint:int ):
    """ This implementation bit_length is a list-oriented view of bint.
        Note that MicroPy lacks bit_length entirely. 
        
        For bitmask purposes, a zero is FALSE and not
        just no value and has length 1 rather than 0.
            
        In most cases, effecive bit_length is ceil(log(x,2)).
    """
    
    if not is_bitint(bint):
            return 0          # 0 effectively like None
            
    if bint == 0:
       return 1 # unlike Py bit_length()
       
    lb = log2(bint)  # mpy log2 melts down at 2^127
    lbi = int(lb)
    if lb == lbi: 
            return lbi+1
    return ceil(lb)
    
def bit_length_bin(bint:int):
    """Kludgy looking, works but slow.
       arg 0 even returns len = 1, unlike Python"""
    
    if not is_bitint(bint):
      return 0

    return len(bin(bint)[2:])
    

    
def make_bitint_from_neg( n:int, blength =1):
    """Not sure when this would be used.  Semantics ? """

    if n >= 0:
        return n

    return invert(int(bin(n)[3:],2 ), max(blength, bit_length(n))) 
    

    
   


""" String Formatting Functions """


"""Bitmask idiom for int ->  1 << ( bitlen(int)) 
   or  len(list), or remove top bit int & ( 1 << ( bitlen(int)-1) ) """
    

def make_bitmask( blength=1 ):
    """Need to partial make_bitmask with max length of collection
       of 'binary' ints."""
       
    return int(str( '1'* max(blength, 1)), 2)
    
def make_bitmask_for( x:int, blength = None ):

    blen = blength or bit_length(x)

    return make_bitmask(blen)
    
def zfill(x:int, maxlen=None):
    """ Make string of 1/0 for int x, filling zeros to left.
            For upython, dumb but nails it and can also work as
            zfill of last resort."""
    
    if maxlen is None: return None  # use bit_length default ?
    
    s = []
    for i in range(maxlen):
        if x & power2(i) == 0:
            s.insert(0, '0')
        else:
            s.insert(0, '1') 
                     
    return ''.join(s)


def bform( x:int, maxlen=None ):
    """Formatter for bitint types, with maxblen option."""

    maxblen = maxlen or bit_length(x)
    try:
        return format(x, 'b').zfill(maxblen)
    except: # upython
        return zfill(x, maxblen)


""" Functions to Compare Bitwise Integers"""

""" Possible for the log func to blow up with large numbers, 2^1000 or so ?"""

def one_of( x:int, y:int ):
    """Only one of x in y. """
    if x == 0 or y ==0: return False
    t = log2(x & y)
    return t == floor(t)
    

def morethanone_of( x:int, y:int ):
    """More than one of x in y. """
    if x == 0 or y==0: return False
    t = log2(x & y)
    return t != floor(t)
    
def all_of( x:int, y:int ):
    """All of x in y"""
    if x == 0: return False 
    return x & y == x

def any_of( x:int, y:int ):
    """Any of integer x in y. """
    return x & y > 0

def none_of( x:int, y:int ):
    """None of x in y."""
    return x & y == 0

"""Basic 'vector' operations on bit integers"""

def diff( x:int, y:int ):
    """( 1, 0 ) or ( 0, 1 ), but not both nor neither ( XOR )"""
    return x ^ y

def match( x:int, y:int ):
    """Like all_of, but returns value rather than bool"""
    return x & y
    
def invert( x:int, blength=1 ):
    """Logical ones-complement, not '~' which sets neg. bit"""
    
    if x < 0: return 0  
    if x == 0: return 1
    
    length = max(bit_length(x), blength)
    
    return x ^ make_bitmask_for(x, length)

def distance(x:int, y:int):
    """A quick and easy bit-integer version of Hamming Distance that
       works with python big ints. The definition of HD is the
       distance between two strings. This version works only with
       bit integers.
       
       Useful for matching.  How matched is it ? """
       
    if not is_bitint(x) or not is_bitint(y):
        return None
       
    return bit_count(diff(x,y))

    
""" Under Dev: Bit 'Slicing' Operations, not fond of these.  Better/Faster ? """

def remove_bit_bin(bint:int, slot:int):
    """Strings make it trivial but it works and may be useful.
       Slot starts with 0, like base 2 exponents"""
    
    if x == 0: return 0
    if x == 1 and slot == 0: return 0
    
    bstr = bin(bint)[2:]
    # print('bstr', bstr)
    
    blen = len(bstr)
    # print('blen ', blen )
    if slot > blen-1: return bint
    
    # print('bstr[:blen-slot-1]', bstr[:blen-slot-1])
    # print('bstr[blen-slot:] ', bstr[blen-slot:])
    
    return int(bstr[:blen-slot-1]+bstr[blen-slot:],2)


def insert_bit_bin(bint:int, slot:int, value:int):
    
    if value not in [ 0, 1 ]:
        return None
    
    bstr = bin(bint)[2:]
    # print('bstr', bstr)
    
    blen = len(bstr)
    # print('blen ', blen )
    
    vstr = str(value)
    
    if slot > blen:
        vstr += '0' * (slot - blen)
        return int(vstr + bstr,2)
        
    # print('bstr[:blen-slot]', bstr[:blen-slot])
    # print('vstr ', vstr)
    # print('bstr[blen-slot:] ', bstr[blen-slot:])
    
    return int(bstr[:blen-slot]+vstr+bstr[blen-slot:],2)

"""Maybe better than the bin versions in terms of binary purity,
   but maybe faster on mpy, probably not on python ...""" 
    
def bit_remove(bint:int, index:int):
    """Delete a single bit """
    
    if bint == 0: return 0
    if index > bit_length(bint)-1 or index < 0: return bint
    
    # print(bint, bin(bint), index)
    # print('left ', bin((bint >> index+1 )))
    # print(bin((bint >> index )<< (index) ))
    # print('right ', bin(bint&(2**index-1)))
    
    x = (bint >> index+1 ) << index | bint & (power2(index)-1)
    
    # print(bin(bint), index, bin(x))
    
    return x
    
    
def bit_insert(bint:int, index:int, value=1):
    """insert single bit before index.  value default is 1, implies an action."""
    
    if not is_bitint(bint) or value not in [ 0, 1 ] or index < 0:
        return None  # use None as error
    
    if index > bit_length(bint)-1 and value > 0: return bint | power2(index)
    
    # print(bint, bin(bint), index, value)
    # print('shiftright ', bin((bint >> index )))
    # print('shiftright + left ', bin((bint >> index )<<1))
    # print('or val ', bin(((bint >> index ) << 1) | value )) 
    # print('shiftleft ', bin((((bint >> index ) << 1 ) | value )  << index ))
    # print('bint right mask ', bin(bint&((2**index)-1)))
    
    x = (((bint >> index ) << 1 ) | value ) << index | bint & (power2(index)-1 )
    
    # print(bin(bint), index, bin(x))
    
    return x
    

    
    


if __name__=='__main__':

    nl()
    nl()
    print('==================================')
    print("=== Test Script for 'BitLogic' ===")
    print('==================================')
    nl()
    
 
    nl()
    nl()

    
    print('=== Functions ===')
    nl()
    a = int(0b11101100000111)
    b = int(0b10000000000000)
    c = int(0b10100000000100)
    d = int(0b00001111000000)
    o = int(0b00000000000001)
    z = int(0b00000000000000)
    
    print('bit_length')
    nl()
    
    bbform = partial( bform, maxlen=16)
    
    print('Using bbform partialled to length 16')
    nl()
    print('a: ', bbform(a), '  bit_length(a) ', bit_length(a))
    print('b: ', bbform(b), '  bit_length(b) ', bit_length(b))
    print('c: ', bbform(c), '  bit_length(c) ', bit_length(c))
    print('d: ', bbform(d), '  bit_length(d) ', bit_length(d))
    print('o: ', bbform(o), '  bit_length(o) ', bit_length(o))
    print('z: ', bbform(z), '  bit_length(z) ', bit_length(z))
    nl()
    
    print('bit_length 4.3:  ', bit_length(4.3))
    print('bit_length None: ', bit_length(None))
    nl()
    
    blist = [ a, b, c, d, o ,z ]

    print('bbform = partial( bform, maxlen=14)')
    bbform = partial( bform, maxlen=14)
    pmake_bit_mask = partial( make_bitmask, blength=14)  

    nl()
    print('bbform(blist)')
    nl()
    print('a: ', bbform(a))
    print('b: ', bbform(b))
    print('c: ', bbform(c))
    print('d: ', bbform(d))
    print('o: ', bbform(o))
    print('z: ', bbform(z))
    nl()
    
    print('one_of x in  y') 
    nl()
    print('one_of(b,a): ', one_of(b,a))
    print('one_of(d,a): ', one_of(d,a))
    print('one_of(o,a): ', one_of(o,a))
    print('one_of(a,a): ', one_of(a,a))
    print('one_of(b,b): ', one_of(b,b))
    print('one_of(z,b): ', one_of(z,b))
    nl()
   
    print('morethanone_of x in  y, detect conflict') 
    nl()
    print('morethanone_of(b,a): ', morethanone_of(b,a))
    print('morethanone_of(d,a): ', morethanone_of(d,a))
    print('morethanone_of(o,a): ', morethanone_of(o,a))
    print('morethanone_of(a,a): ', morethanone_of(a,a))
    print('morethanone_of(b,b): ', morethanone_of(b,b))
    print('morethanone_of(z,z): ', morethanone_of(z,z))
    nl()
    
    print('all_of x in y, logical AND = x ')
    nl()
    print('all_of(b,a): ', all_of(b,a))
    print('all_of(c,a): ', all_of(c,a))
    print('all_of(d,a): ', all_of(d,a))
    print('all_of(a,a): ', all_of(a,a))
    print('all_of(o,a): ', all_of(o,a))
    print('all_of(z,z): ', all_of(z,z))
    nl()
    
    print('any_of x in y, logical AND > 0 ')
    nl()
    print('any_of(c,b): ', any_of(c,b))
    print('any_of(d,b): ', any_of(d,b))
    print('any_of(o,d): ', any_of(o,d))
    print('any_of(a,a): ', any_of(a,a))
    print('any_of(z,a): ', any_of(z,a))
    print('any_of(z,z): ', any_of(z,z))
    nl()
    
    print('none_of x in y - logical NAND')
    nl()
    print('none_of(d,c): ', none_of(d,c))      
    print('none_of(d,a): ', none_of(d,a))
    print('none_of(o,a): ', none_of(o,a))
    print('none_of(a,a): ', none_of(a,a))
    print('none_of(z,a): ', none_of(z,a))
    print('none_of(z,z): ', none_of(z,z))
    nl()
    
    print('diff between x and y - logical XOR')
    nl()
    print('diff(d,b): ', bbform(diff(d,b)))      
    print('diff(d,a): ', bbform(diff(d,a)))
    print('diff(o,a): ', bbform(diff(o,a)))
    print('diff(a,a): ', bbform(diff(a,a)))
    print('diff(z,a): ', bbform(diff(z,a)), '  compare to invert(a): ', bbform(invert(a)))
    print('diff(z,z): ', bbform(diff(z,z)))
    nl()
    print('match() returning int of matches, similar to all_of')
    nl()
    print('match(d,b): ', bbform(match(d,b)))      
    print('match(d,a): ', bbform(match(d,a)))
    print('match(o,a): ', bbform(match(o,b)))
    print('match(a,a): ', bbform(match(a,a)))
    print('match(z,a): ', bbform(match(z,a)))
    nl()
    
    print('To Invert Or Not ')
    nl()
    
    print('Invert combined with logical functions ') 
    print('match( a , invert(a)): ', bbform(match( a , invert(a))))
    print('any_of( a, invert(a)):   ', any_of( a, invert(a)))
    print('none_of( a, invert(a)):   ', none_of( a, invert(a)))
    nl()
    
    print('The Reason We Invert')
    nl()
    print('a:         ', bbform(a))
    print('invert(a): ', bbform(invert(a)))
    print('b:         ', bbform(b))      
    print('invert(b): ', bbform(invert(b)))
    print('o:         ', bbform(o))      
    print('invert(o): ', bbform(invert(o)))
    print('z:         ', bbform(z)) 
    print('invert(z): ', bbform(invert(z)), 'pythonically wrong, but right for bitint or in blist')
    print('bool(invert(z)): ', bool(invert(z)))
    nl()
    
    print('Comparing ones to twos complement Python')
    nl()
    print('~0: ', ~0)
    print('~0 == -1: ', ~0 == -1)
    print('~-1 ', ~-1)
    print('~~0 ', ~~0)
    print('bin(~0) ', bin(~0))
    print('bin(-1) ', bin(-1))    
    print('bool(~0) ', bool(~0))
    print('bool(-1) ', bool(-1))
    # print('bool(bin(~0)) ', bool(bin(~0)))
    nl()
    print('invert(0) ', invert(0))
    print('invert(~0) ', invert(~0))
    nl()
    
    print('bitlength(0) ', bit_length(0))
    print('bitlength(1) ', bit_length(1))
    nl()
    
    print('make_bitmask_for(0)    ', bin(make_bitmask_for(0)))
    print('1^make_bitmask_for(0)  ', bin(1^make_bitmask_for(0)))
    print('make_bitmask(0))       ', bin(make_bitmask(0)))
    print('make_bitmask(4))       ', bin(make_bitmask(4)))
    print('1^make_bitmask(4)      ', bin(1^make_bitmask(4)))
    print('1^int(0b1111)          ', bin(1^int(0b1111))) 
    nl()
    
    print('Test for genrandint(), size is base 2^size.')
    nl()
    for i in [ 0, 1, 2, 3, 4, 7, 30, 31, 32, 33, 59, 60, 61, 63, 64, 100 ]:
        x = genrandint(i)
        print('randint for size ', i,' = ' , x, ',  bit_length = ', bit_length(x) )
    nl()
    

    
    print('Running bit_indexes, bit_count and one_bit_set.')
    nl()
    for i in [ 0, 1, 2, 3, 7, 8, 2**100, 88885555 ]:
        print('integer', i)
        print(bin(i))
        print('bit_indexes: ', bit_indexes(i))
        print('Check bit_count: ', len(bit_indexes(i)), bit_count(i))
        print('One bit set: ', one_bit_set(i))
        nl()

    x = 0
    for i in bit_indexes(88885555):
        x += power2(i)
        
    print('Reconstructing integer from indexes, should be 88885555:', x )
    nl()
    print('Test "hamming-like" distance')
    nl()
    
    x = 2**16+15
    y = 2**17+1
    z = 0
    m = -22

    print('x: ', bin(x), '   bit count: ', bit_count(x))
    print('y: ', bin(y), '   bit count: ', bit_count(y))
    print('z: ', bin(z), '   bit count: ', bit_count(z))
    print('m: ', bin(m), '   bit count: ', bit_count(z))
    nl()
    print('diffxy: ', bin(diff(x,y)))
    print('diffyx: ', bin(diff(y,x)))
    print('diff bit count: ', bit_count(diff(x,y)))
    nl()
    print('distance x,y : ', distance(x,y))
    print('distance y,x : ', distance(y,x))
    print('distance x,z : ', distance(x,z))
    print('distance z,y : ', distance(z,y))
    print('distance m,y : ', distance(m,y))
    print('distance "hello","world" : ', distance('hello','world'))
    nl()

    print('Test bin-based remove_bit')
    nl()
    
    val = 11327
    slot = 7
    # print('Using int ', val, bin(val) , 'slot ', slot )
    # print('bit indexes ', bit_indexes(val))
    nl()

    
    x = remove_bit_bin(val, slot)
    if x is not None:
        print('value ', val, bin(val), ' slot ', slot )
        print('bit indexes ', bit_indexes(val))
        print('new value ', x, bin(x))
        print('bit indexes ', bit_indexes(x))
        print('bit length ', bit_length(x))
    else:
        print(x)
    nl()
        
    print('Test bin-based insert_bit')
    nl()
        
    y = insert_bit_bin(val, slot, 1)
    print('value ', val, bin(val), ' slot ', slot )
    print('bit indexes ', bit_indexes(val))
    print('new value ', y, bin(y))
    print('bit indexes ', bit_indexes(y))
    print('bit length ', bit_length(y))
    nl()
    
    print()
    print('Testing bit-op bit_remove')
    print()

    for i in [ 0, 1, 5, 7, 8, 11, 17, 21 ]:
        print()
        for j in [ 0, 1, 2, 3, 7 ]:
            x = bit_remove(i, j)
            print('bit_remove: bintint', bin(i), 'index', j, 'returned ', bin(x) )
            # print()

    print()
    print('Testing bitip bit_insert')
    print()

    for i in [ 0, 1, 4, 7, 11, 14, 21 ]:
        print()
        for j in [ 0, 1, 2, 6 ]:
            c = choice([0, 1 ])
            x = bit_insert(i, j, c )
            print('bit_insert: bitint', bin(i), ' index', j, 'value', c, ' returned ', bin(x) )
            # print()
    print()
    
    testints = ['hello', -1, ~0, 1.7, 0, 1, 2, 3, 4, 5, 227]
   
    print('Test power2 function')
    
    for i in testints:
        print('power2 ', i ,' = ', power2(i))
    print('pow(2, 227)  = ', pow(2,227))
    nl()
    
    print('Test logar2 function')
    
    for i in testints:
        print('logar2 ', i ,' = ', logar2(i))
    print('log2(227)  = ', log2(227))
    nl()
    
    print('bit_length_alt vs. bit_length, vs py_bitlength, vs bit_length_bin')
    nl()
    
    testints = [-333, -1, ~0, 0, 1, 2, 3, 4, 5, 15, 16, 227, 2047, 2048, 877773331]
    
    try:
        X = 123
        x = x.bit_length()
        py_bitlen_avail = True
    except:
        py_bitlen_avail = False   
        
    if py_bitlen_avail:
        for i in testints:
            print(i, 'bit_length_alt: ', bit_length_alt(i), 'bit_length', bit_length(i) , 'bit_length_bin ', \
                    bit_length_bin(i), 'bit_length_chunk ', bit_length_chunk(i),  'py_bitlen ', i.bit_length())
            
    else:    
        for i in testints:
            print(i, 'bit_length_alt: ', bit_length_alt(i), 'bit_length', bit_length(i), 'bit_length_bin ', \
             bit_length_bin(i), 'bit_length_chunk ', bit_length_chunk(i), 'py_bitlen ', 'unavailible')
    nl()    
    
    blength = 6
    print('make_bitint_from_neg, bit length = ', blength)
    nl()
    for i in [ 1, 0, ~0 , -1, -2, -3, -4, -15, -16, -17]:
        print('make bitint from neg ', bin(i), bin(make_bitint_from_neg( i, blength)))
    nl()
    
    """ 

    print('=== Bit Operations ===')
    nl()
    

    
    for i in [ 0, 1, 2, 3, 7, 16 ]:   # [ 0, 1, 2, 3, 15, 16 ,17, 222 ]
        print('BitOps for i = ', i, bin(i))
        nl()
        for n in [ 0, 1, 2, 3, 7 ]:   # [ 0, 1, ,2, 3, 5, 7 ]
            print('int = ', bin(i) )
            print( 'bit_get ', n, bin(bit_get( i, n )))
            print( 'bit_set ', n, bin(bit_set( i, n )))
            print( 'bit_clear ', n, bin(bit_clear( i, n )))
            print( 'bit_toggle ', n, bin(bit_toggle( i, n )))
            nl()    
    
    """
    
    nl()
    print('The End.')
    nl()

