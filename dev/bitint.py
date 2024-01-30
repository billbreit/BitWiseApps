
"""

BitInt, an idealized bit integer class. 

Ones-complement wrapper for Python standard twos-complement logic,
mostly useful for debugging and displaying an int or BitInt in
binary form, and learning about the binary integer approach to logic.

Runs on Python 3.9 and micropython v1.20.0 on a Pico.

module:     bitint
version:    v0.3.3
sourcecode: https://github/billbreit/BitWise
copyleft:   2023 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer
    
"""

try:
    from utils import fix_paths
except:
    from dev.utils import fix_paths
fix_paths()
    
    
from dev.bitlogic import power2, partial, bit_length, zfill, invert, make_bitmask, bform  


nl = print
DEBUG = False


class BitLogicError(Exception):
    pass
    
class BitInt(object):
    """BitInt wraps an inner int with bitwise logical functions only,
       no arithmetic functions.  This class is mostly for debugging
       and would not be deployed outside development. """  

    def __init__(self, an_integer, *args, **kwargs ):
    
        super().__init__(*args, **kwargs)

        if an_integer <= ~0:
            raise BitLogicError('Negative values and `0 ( minus zero ) are not BitInt numbers.')

        self._int = int(an_integer)
    
    @classmethod    
    def int(cls, other):
        """ Type scrubbing, bit kludgy but necessary"""
        if isinstance(other, BitInt):
            return other._int
        else:
            return int(other)
            
    def __and__(self, other ):
        """Bitwise AND of x & y """
        return self._int & self.int(other)
            
            
    def __or__(self, other):
        """Bitwise OR of x | y."""
        return self._int | self.int(other)
 
        
    def __xor__(self, other):
        """Bitwise XOR of x ^ y, either x or y but not x & y"""
        return self._int ^ self.int(other)
            
    def __invert__(self ):
        """Bitwise inverse ~x ( tilde x ) of the number x.
        
           Note non-standard ones-complment implementation:
           
           bin(12) is '0b1100'
           bin(~12) is '-0b1101', negative binary
           invert(12) is '0b0011'
           
           Twos-complement works fine and is more efficient,
           but ones-complement is easier to debug.

        """
        
        if self._int==0: return 1  
        
        return invert(self._int) 
        
    def __lshift__( self, offset:int):
        """x shifted left by offset, x<< y."""
        return self._int << offset
        
    def __rshift__(self, offset:int):
        """x shifted right by offset, x >> y."""
        return self._int >> offset
        
    ''' i_funcs cause parsing errors. could implement but something
        badly stateful lurks here ...
        
    def __iand__(self, other):
        """x = iand(x, y) is equivalent to x &= y
           Alters the vaule of underlying _int """
        self._int &= self.int(other)
        
    def __ixor__(self, other):
        """x = ixor(x, y) is equivalent to a ^= b.
           Alters the vaule of underlying _int """
        self_int ^= self.int(other)
        
    def __ilshift__(self, offset):
        """x = lshift(x, y) is equivalent to x <<= y.
           Alters the vaule of underlying _int """
        self._int <<= offset
        
    def __ior__(self, other):
        """x = ior(x, y) is equivalent to x |= y.
           Alters the vaule of underlying _int """
        self._int |= self.int(other)
        
    def __irshift__( self, offset):
        """x = rshift(x, y) is equivalent to x >>= y.
           Alters the vaule of underlying _int """
        self._int >>= offset
        
        '''

    def __iter__(self):
        """Returns a list of 1/0 values representing the sequence of bits set
           in the underlying integer.
           
           ex. the comprehension [ v for v in iter(11) ] where 11 = '0b1011'
           would return the sequence [1, 1, 0, 1 ], reversed from 'b' format.
           The expression:

                numb = 0
                for i, v in enumerate([1, 1, 0, 1 ]):
                    if v == 1:
                        numb |= pow(2, i )
                print(numb)
                
                will recover the int(11).
             
         """ 

        # print('iter- for self ', self)
        # print('iter- bin(self) ', bin(self))
        # print('iter- bit_length ', self.bit_length)
        # nl()

        for bindex in range(self.bit_length):
        
            # print('iter- bindex ', bindex)
            test = power2(bindex) & self._int
            if test == 0:
                yield 0
            else:
                yield 1
                
    @property
    def value(self):
        return self._int
                            
    @property
    def bit_length( self ):
        return bit_length(self._int)
            
    @property
    def num_bits_set(self):

        bl = [ v for v in iter(self) ]
        return bl.count(1)    # faster than sum ?
    
    @property       
    def bin(self):
        return bin(self._int)
                            
bitint = BitInt 


class BitList( list ):
    """Basically, a formatter for a list of 'binary' ints, implementing 
       max_length ( max length some 'ones complement' functions. The int
       in the list have a context/state ( max_length ) in that leading
       zeros are significant even if 'false/0', but are just 'not there'
       for a single 0-value integer.
     """

    @property
    def max_length(self):
        """Bit length of largest int element in the list"""
        
        try:
            return max(max(self).bit_length(), 1)
        except:  # upython  
            max_len = max([ bit_length(i) for i in self ]) 
            return max(max_len, 1)           
    
    def make_bitmask( self ):
        """ Bit_mask of binary ones with max length in collection
                of 'binary' ints. Inverting leading 0 to 1 is significant."""
        return int(str( '1'* self.max_length), 2)
    
    def form( self, x:int ):
            
        try:
            return zfill(x, 'b').zfill(self.max_length)
        except: # upython
            return zfill(x, self.max_length)
                    
bitlist = BitList


"""Found code ( on stackoverflow ) Experimental Stuff, doesn't work with micropython """

def text_to_bits(text, encoding='utf-8', errors='surrogatepass'):
    bits = bin(int.from_bytes(text.encode(encoding, errors), 'big'))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def bits_to_text(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode(encoding, errors) or '\0'
    
"""  not working on mpy, no str.zfill
print('Quick test of text/bits')
bits = text_to_bits('Hello World /n I\'m the %$^&@##$* Slime That Comes Out of Your TV ! ')
print(bits)
print(int(bits,2))
print(hex(int(bits,2)))
print(int(hex(int(bits,2)),16))
nl()
text = bits_to_text(bits)
print(text)
"""



if __name__=='__main__':

    nl()
    nl()
    print('==================================')
    print("=== Test Script for 'BitLogic' ===")
    print('==================================')
    nl()
    
    def bit_info(bint):
            print('bint ', bint)
            print('type(bint) ', type(bint))
            print('bint.value ', bint.value)
            print('bint.bin ', bint.bin)
            print('bint.bit_length ', bint.bit_length)
            print('bint.num_bits_set ', bint.num_bits_set)
            nl()
     
    nl()
    print('=== Test BitInt Class ===')
    nl()
    
    print('bi = bitint(25)')
    nl()
    bi = bitint(25)
    
    print('dir(bi) ', dir(bi))
    nl()
    bit_info(bi)
    print('isinstance(bi, int) ', isinstance(bi, int))
    nl()
    
    itest = bitint(33) # not working
    # itest = 33
    
    bform6 = partial(bform, maxlen=6 )
    print('Test non-destructive dunder methods')
    nl()
    print('bi and itest ', bform6(bi), bform6(itest))
    nl()
    
    print('bi & itest  ', bi & itest, bform6(bi & itest))
    print('bi | itest  ', bi | itest, bform6(bi | itest))
    print('bi ^ itest  ', bi ^ itest, bform6(bi ^ itest))
    print('bi << 1     ', bi << 1,    bform6(bi << 1))
    print('bi >> 1     ', bi >> 1,    bform6(bi >> 1))
    nl()
    
    print('Test destructive dunder methods')
    nl()
    print('Invalid syntax. Commented out for now. may get rid of.')
    nl() 
    
    """
    print('bi &= itest', bi &= itest)
    bi = bitint(25)
    print('bi |= itest', bi |= itest)
    bi = bitint(25)
    print('bi ^= itest', bi ^= itest)
    bi = bitint(25)
    print('bi <<= 1', bi <<= 1)
    bi = bitint(25)
    print('bi >>= 1', bi >>= 1)
    nl()
    bi = bitint(25)
    """
   
    bit_info(bitint(0))
    bit_info(bitint(255))
    bit_info(bitint(333315))
    nl()

    print('try bitint(44) + 23')
    nl()
    x = bitint(44)
    try:
        y = x + 23
    except Exception as e:
        print(e)
    nl()
    
    print('try x = bitint(-1)  ')
    nl()
    
    try:
        x = bitint(-1 )
    except BitLogicError as e:
        print(e)
        nl()
    
    print('try x = bitint(-111)  ')

    try:
        x = bitint(-111 )
    except BitLogicError as e:
        print(e)
        nl()
    else:
        print('No Error')
        nl()

    print('Test for BitInt method bi.__iter__')
    nl()
    print('bin(bi) ', bi.bin)
    print('bi.bit_length ', bi.bit_length)
    print('bi.num_bits_set ', bi.num_bits_set)
    nl()
    for bindex in iter(bi):
            print('__iter__ func returned ', bindex)
    nl()
    
    ilist = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight' ]
    
    print('Using BigInt to map into a list', ilist)
    nl()
    
    o = int(0b01010101)
    e = int(0b10101010)
    
    odd_index = bitint( o )
    even_index = bitint( e )
    
    print('odd_index ', odd_index, '  ', odd_index.bin)
    print('even_index ', even_index, '  ', even_index.bin)
    nl()
    print('Note the bit lengths of odd and even are ', odd_index.bit_length, even_index.bit_length)  
    print('odd_index.num_bits_set  ',  odd_index.num_bits_set)
    print('even_index.num_bits_set ',  even_index.num_bits_set)
    nl()

    nl()

    print('Using iter(odd_index) ', odd_index.bin ,' to fetch odds from list') 
    nl()
    
    # better ways to do, bitlogic bit_indexes
    olist = []
    for i, v in enumerate(iter(odd_index)):
        print('odds', v)
        if v == 1:
                olist.append(ilist[i])
    nl()
                    
    print('Using iter(even_index) ', even_index.bin, ' to fetch evens from list') 
    nl()
            
    elist = []      
    for i, v in enumerate(iter(even_index)):
        print('even', v)
        if v == 1:
                elist.append(ilist[i])
    nl()
                
    print('odds ', olist)
    print('evens ', elist)
    nl()
    
   
    print('=== bitlist class and bform ===')
    nl()
    
    a = int(0b11101100000111)
    b = int(0b10000000000000)
    c = int(0b10100000000100)
    d = int(0b00001111000000)
    o = int(0b00000000000001)
    z = int(0b00000000000000)

    blist = bitlist( [z, z, z, z] )
    print('blist ', blist )
    print('blist max_length: ', blist.max_length)
    print('blist make_bitmask: ', blist.form(blist.make_bitmask()))
    nl()



    blist = bitlist( [a, b, c, d] )
    print('new blist ', blist )     
    print('blist max_length: ', blist.max_length)
    print('blist make_bitmask: ', blist.form(blist.make_bitmask()))
    nl()
    
    
    print('bbform, bform partialled to length blist.max_length')
    nl()
    bbform = partial( bform, maxlen=blist.max_length)
    for i, bint in enumerate(blist):
        print('slot', i, ' = ', bbform(bint))
    nl()

    print('bform with some manipulations.')
    nl()
    print('bform(int)            ', bform(int(0b0101011101111001110001110)))
    print('bform(invert(int, 24) ', bform(invert(int(0b0101011101111001110001110)), 24), '   length 24')
    print('bform(invert(int)     ', bform(invert(int(0b0101011101111001110001110))), '    length becomes 23')
    nl()
    print('Not working with CircuitPython, bad partial function ? ')

    pmake_bit_mask = partial( make_bitmask, blength=blist.max_length) 
    

    nl()
    nl()
    print('End of Test')

