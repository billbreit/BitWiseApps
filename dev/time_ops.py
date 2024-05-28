"""Basic performance reality test for builtins and bitlogic.py functions,
 should work with both Python and micropython, except for py_bit_length,
  roughly 10X faster than Python versions, so far. Python's log2 comes off
  pretty well. power2 is the big winner ( ints only ).  logar2_hybrid seems
  to break the 2^127 barrier.  bin() is fast on Py39 but very slow on mpy platforms.
  
  Something odd about bitslice functions - they are too fast.  There must be
  a large amount of hidden loop overhead.  The ops in big_formula_time also
  don't quite add up ... keep on testing."""

import time

import math

from random import randrange, choice, randint

try:
    from utils import fix_paths
except:
    from dev.utils import fix_paths
fix_paths()
    
try:
    from bitlogic import genrandint
except:
    from dev.bitlogic import genrandint
    
try:
    x = (2).bit_length()
    py_bitlen_avail = True
except:
    py_bitlen_avail = False
    
try:
    from micropython import const
except:
    const = lambda x : x
    
try:
    x = '111'.zfill(10)
    zfill_avail = True
except:
    zfill_avail = False


    
nl = print

"""

print(dir(time))
print()
print('gmtime:    ', time.gmtime())
print('localtime: ', time.localtime())
print('mktime:    ', time.mktime(time.localtime()))
print('Sleeping 2 sec ')
time.sleep(2)
print('time:      ', time.time())
print('type(time):', type(time.time()))
prev = time.time_ns()
print('base time_ns: ', prev)
time.sleep(.5)
for i in range(10):
    current = time.time_ns()
    print('diff time_ns in usecs: ', (current-prev)/1000)
    prev= current
    time.sleep(.5)

"""
    
""" Wrapper """


# import time

scale_msec = const(1000000)
 
  
def timer(func, repeat=1): 
    """This function shows the execution time of the function object passed."""
    # Repeat doesn't work for @timer(repeat=123), only as call.
    
    def wrapped_func(*args, **kwargs): 
        t1 = time.time_ns()
        for _ in range(repeat):
            result = func(*args, **kwargs) 
        t2 = time.time_ns() 
        print(f'Timed {func.__name__!r} repeated {repeat} times: {(t2-t1)/scale_msec} msecs.') 
        return result
         
    return wrapped_func 

print()

"""Note that each these factors ( scale, density, num_elements ) effect most python
   runtimes are more or less linearly by themselves. Bit density in core bitwise ops
   is more or less linear.  However, when the factor are combined into the multiplier
   ( scale x bit_density x num of elements ), the result can be exponential.  The
   bit_indexes functions are exponential for scale x bit_density.  On the other hand,
   the bit_insert and bit_remove functions are almost invariant to scale x bit_density
   in 2^200 scale ints. 
   
   There is also signifcant performance hurtle for builtin operations requiring float
   conversion (pow/log2), in addition to the hard limit of float(2^127) in mpy.
   """
   
scale = const(200)   # creates 2^scale integers, mpy log blowup at 2^127
bit_density = const(20)  # density of bits, mainly for bit_indexes testing
num_of_elements = const(100)
inner_repeat = const(10)
assert num_of_elements >= inner_repeat, "Repeat must be less than num elements."


MPY_MAX_POWER = const(127)
MPY_MAX_VALUE = math.pow(2, 127)

print('scale ', scale )
print('bit density ', bit_density)
print('number of elements', num_of_elements )
print('repeats ', inner_repeat )
print()

@timer
def no_op_loop(n): 
    for i in range(n): 
        for j in range(num_of_elements):
            # x = j   # tiny load takes about 30% more than pass
            pass

  
@timer
def mult_time(n):   
    for i in range(n): 
        for j in range(num_of_elements):
            # x = i*j  # allow int, about 2-3x faster
            x = i*(j+.1)  # force float conversion
            
@timer
def div_time(n): 
    for i in range(1, n+1): 
        for j in range(num_of_elements): 
            x = j/i
            
big_floats = [ randrange(10**9)/(3.3) for i in range(num_of_elements)]

# print(big_floats)

randfloat = choice(big_floats)
# print(randfloat)
            
@timer
def big_mult_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = big_floats[j]*randfloat 
            
@timer
def big_div_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = big_floats[j]/randfloat
            
@timer
def big_formula_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = (big_floats[j]*(randfloat+i)/(big_floats[j]+(randfloat*i)-n))

            
def build_powersof2(number_of_ints, scale, density=None):
    assert density <= scale, \
           "density (num bits on) must be less than or eq scale ( bit length)."
    po2 = []
    for i in range(number_of_ints):
        x = 0
        for j in range(density):
            x |= 1<< randint(0,scale)
        po2.append(x)
    
    return po2

powersof2 = build_powersof2( num_of_elements, scale, bit_density)

@timer
def and_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = powersof2[i] & powersof2[j]
            
@timer
def andnot_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = powersof2[i] & ~powersof2[j]
         
@timer
def or_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = powersof2[i] | powersof2[j]
            
@timer
def xor_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = powersof2[i] ^ powersof2[j]
            
@timer
def rshift_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = powersof2[j] >> j

def bit_length(bint:int):
    """bit_length_alt in bitlogic.py.  Slow, log2 5x faster,
       but mpy int to float infinity error at 2**127 """
       
    if bint == 0:
        return 1 # unlike Py bit_length()
            
    blen = 0
    while bint > 0:
        bint >>= 1
        blen += 1
    return blen
    
def bit_length_shift(bint:int):
    """bit_length_alt in bitlogic.py.  Slow, log2 5x faster,
       but mpy int to float infinity error at 2**127 """
       
    if bint == 0:
        return 1 # unlike Py bit_length()
            
    blen = 0
    while (bint >> blen) > 0:
        blen += 1
    return blen

def bit_length_chunk(bint:int, chunk_size:int = 12):
    """like above with chunking, chunk_size=12 from T&E """
    
    blen = 0
    chunk = 2**chunk_size
    
    while bint > chunk:
        bint >>= chunk_size
        blen += chunk_size
        
    while bint > 0:
        bint >>= 1
        blen += 1
        
    return blen
            
def bit_length_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_length(powersof2[j])
            
def bit_length_shift_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_length_shift(powersof2[j])
            
def bit_length_chunk_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_length_chunk(powersof2[j])
             
def bit_length2( bint ):
    """math.log(2**128, 2) -> infinity"""

           
    if bint == 0:
        return 1 # unlike Py bit_length()
    
    lb = math.log2(bint)
    lbi = int(lb)  # can't convert inf to int
    if lb == lbi: 
            return lbi+1
    return math.ceil(lb)

def bit_length3( bint ):
    """math.log(2**128, 2) -> infinity"""

           
    if bint == 0:
       return 1 # unlike Py bit_length()
       
    return math.floor(math.log2(bint))

def bit_length_logar_hybrid( bint ):
    """math.log(2**128, 2) -> infinity"""

           
    if bint == 0:
       return 1 # unlike Py bit_length()
       
    return logar2_hybrid(bint) + 1


def bit_length2_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_length2(powersof2[j])

            
def bit_length_logar_hybrid_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_length3(powersof2[j])
            
def bit_length_logar_hybrid_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_length_logar_hybrid(powersof2[j])

            
def bit_length_bin(bint:int):
    """Kludgy looking, works fast on py39 but slow on mpy.
       arg 0 even returns len = 1, unlike Python"""
    
    return len(bin(bint)[2:])

def bit_length_bin_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_length_bin(powersof2[j])

            
def py_bit_length_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = powersof2[j].bit_length()
            
            
# @timer()
def pow2_time(n):
    for i in range(n): 
        for j in range(num_of_elements):
            # x = math.pow(2,j)  # meltdown at 2^128            
            x = pow(2,j)   # slow   
            # x = 2**j   # slightly faster
            
def power2_time(n):
    """Much faster, about 10x, only works with integers"""
    for i in range(n): 
        for j in range(0, scale):
            x = 1 << j  
            
def log_time(n): 
    for i in range(n): 
        for j in range(num_of_elements): 
            x = math.log(powersof2[j],2) #divide by zero ?
            # x = math.log(j)
            
def log2_time(n): 
    for i in range(1, n): 
        for j in range(num_of_elements): 
            x = math.log2(powersof2[j])
            
"""logar2 is a 'top bit' or 'leftmost bit' function, equiv to floor(log2())"""

def logar2(bint:int) -> int:
    """Replace log2 with int-powered function, only works with ints.""" 
    
    # return bit_length2(bint) - 1
    return bit_length3(bint) - 1 
    # return bit_length_chunk(bint) - 1  # about 40% faster

def logar2_time(n):
    
    for i in range(1, n): 
        for j in range(num_of_elements): 
            x = logar2(powersof2[j])
            

    
# Best of Breed Award           
def logar2_hybrid(bint:int) -> int:
    """Replace log2 with int-powered function, avoids 2^127
       int->float meltdown on mpy, only works with ints.""" 
    
    if bint == 0: return 0  #  ? or None
    log = 0
    # save_bint = bint
    while bint > MPY_MAX_VALUE:
        log += MPY_MAX_POWER
        bint >>= MPY_MAX_POWER
        
    if bint > 0:
        log += math.floor(math.log2(bint))
        
    # print( 'logar2_h ', save_bint, log )
        
    return log

def logar2_hybrid_time(n):
    
    for i in range(1, n): 
        for j in range(num_of_elements): 
            x = logar2_hybrid(powersof2[j])

    
def bit_count(bint:int):
    """Count number of bits set in a binary integer.
       bin(x).count('1') works for x >= 0. """
    
    count = 0
    while bint > 0:
        bint &= bint - 1
        count += 1
        
def bit_count_time(n):
    
    for i in range(1, n): 
        for j in range(num_of_elements):
            x = bit_count(powersof2[j])

def bit_count_bin(bint:int):
    """Count number of bits set in a binary integer.
       bin(x).count('1') works for x >= 0. """
    
    return bin(bint)[2:].count('1')

        
def bit_count_bin_time(n):
    
    for i in range(1, n): 
        for j in range(num_of_elements):
            x = bit_count_bin(powersof2[j])
            

def bit_indexes_logar_hybrid(bint:int):
    """Make list of ints for indexes of bits that are set. Indexes are
       essentially the same as base-2 exponents.
       For example: bitIndexes(23) => [0, 1, 2, 4]
                    2^0 + 2^1 + 2^2 + 2^4 = 23
    """

    bit_indexes = []
    
    save_bint = bint
    
    while bint > 0:
        index = logar2_hybrid(bint)  # top bit
        bint &= (1<<index) - 1
        bit_indexes.insert(0, index)
        # bit_indexes.append(index)

    # return bit_indexes.sort()
    return bit_indexes


def bit_indexes_logar_hybrid_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_indexes_logar_hybrid(powersof2[j])
            

            
def bit_indexes_brute(bint:int):
    """Make list of ints for indexes of bits that are set. Indexes are
       essentially the same as base-2 exponents.
       For example: bitIndexes(23) => [0, 1, 2, 4]
                    2^0 + 2^1 + 2^2 + 2^4 = 23
    """
    
    """Performance looks exponental"""
    
    bit_indexes = []
    index = 0
    while bint > 0:
        if bint&1: bit_indexes.append(index)
        index += 1
        bint >>= 1

    return bit_indexes

def bit_indexes_brute_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_indexes_brute(powersof2[j])
            
def bit_indexes_bin(bint:int):
    
    return [ i for i, j in enumerate(bin(bint)[2:]) if j=='1']

def bit_indexes_bin_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_indexes_bin(powersof2[j])
            
def bit_indexes_bin_time(n):
    for i in range(1, n): 
        for j in range(1,num_of_elements): 
            x = bit_indexes_bin(powersof2[j])
            
def bit_remove( bint, index ):
    return (bint >> index+1 ) << index | bint & (( 1 << index)-1)

    
def bit_insert( bint, index, value=1):
    return (((bint >> index ) << 1 ) | value ) << index | bint & (( 1 << index)-1 )

def bitslice_insert(bint, index, bit_len, value ):
    """Insert before index-th slot""" 
   
    return (((( bint >> index ) << bit_len) | value ) << index ) | bint & (( 1 << index )-1)

def bitslice_insert_bin(bint, index, bit_len, value ):
    """Testing, may not be optimal ? """

    bstr = bin(bint)[2:]
    vstr = bin(value)[2:].zfill(bit_len)
    bstrout = bstr[:index] + vstr.zfill(bit_len) + bstr[index:]
    return int(bstrout, 2 )



def bit_remove_time(n):
    for i in range(0, n): 
        for j in range(0,num_of_elements): 
            x = bit_remove( j, i )
            
        
def bit_insert_time(n):
    for i in range(0, n): 
        for j in range(0,num_of_elements): 
            x = bit_insert( j, i )
            
def bitslice_insert_time(n):
    for i in range(0, n): 
        for j in range(0,num_of_elements): 
            x = bitslice_insert( j, i, 5,  7 )
            
def bitslice_insert_bin_time(n):
    for i in range(0, n): 
        for j in range(0,num_of_elements): 
            x = bitslice_insert_bin( j, i, 5, 7 )

print('Math and Bitwise Ops Tests')
nl()
startt = time.time_ns()
        
no_op_loop(inner_repeat)
mult_time(inner_repeat)
div_time(inner_repeat)
big_mult_time(inner_repeat)
big_div_time(inner_repeat)
big_formula_time(inner_repeat)
and_time(inner_repeat)
andnot_time(inner_repeat)
or_time(inner_repeat)
rshift_time(inner_repeat)
xor_time(inner_repeat)
print()
timer(bit_length_time, repeat=1)(inner_repeat)
timer(bit_length_shift_time, repeat=1)(inner_repeat)
timer(bit_length_chunk_time, repeat=1)(inner_repeat)
# timer(bit_length2_time, repeat=1)(inner_repeat)  # blows up 2^127
# timer(bit_length3_time, repeat=1)(inner_repeat)
timer(bit_length_logar_hybrid_time, repeat=1)(inner_repeat)
timer(bit_length_bin_time, repeat=1)(inner_repeat) # too slow on mpy
if py_bitlen_avail:
    timer(py_bit_length_time, repeat=1)(inner_repeat)
else:
    print('No int.bit_length() availible.')
print()
timer(pow2_time, repeat=1)(inner_repeat)  # too slow
timer(power2_time, repeat=1)(inner_repeat)
timer(log_time, repeat=1)(inner_repeat)
timer(log2_time, repeat=1)(inner_repeat)
# timer(logar2_time, repeat=1)(inner_repeat)  # meltdown at 2^127
timer(logar2_hybrid_time, repeat=1)(inner_repeat)
timer(bit_count_time, repeat=1)(inner_repeat)
timer(bit_count_bin_time, repeat=1)(inner_repeat)
print()
timer(bit_indexes_logar_hybrid_time, repeat=1)(inner_repeat)  
timer(bit_indexes_brute_time, repeat=1)(inner_repeat)  # slowerr than logar
timer(bit_indexes_bin_time, repeat=1)(inner_repeat)  # faster than brute on py, way slow on mpy
print()
timer(bit_remove_time, repeat=1)(inner_repeat) 
timer(bit_insert_time, repeat=1)(inner_repeat)
timer(bitslice_insert_time, repeat=1)(inner_repeat)
if zfill_avail:  # no str.zfill on mpy
    timer(bitslice_insert_bin_time, repeat=1)(inner_repeat) 
    
endt = time.time_ns()

print()
print('Total run time (ms): ', (endt-startt)/scale_msec)
print()
    
# for i in [ 0, 1, 2, 3, 4, 5, 6, 7, 8 ,15, 16 , 9999, 3773344]:
#for i in powersof2:
    # py_bitlen = i.bit_length() if py_bitlen_avail else 'not avail.'
#    print(i, logar2_hybrid(i), bit_length(i)  )


del(powersof2)   # getting thonny.plugins.micropython.mp_back.ManagementError: 

