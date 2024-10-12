
"""Works on MicroPython """

"""
try:
    import bisect
    from bitlogic import bit_length, bit_length_alt
except:
"""

import dev.bisect as bisect
from dev.bitlogic import bit_length, bit_length_alt

from gc import mem_free, mem_alloc


print(dir(bisect))
print()

# x = [ 1, 2, 4, 8, 16, 32, 64]
start_mem = mem_free()
start_alloc = mem_alloc()
print('Start mem: ', start_mem)
print('Start alloc: ', start_alloc)

scale = 300
print('Scale is 2^', scale)

lookup = [ 2**i for i in range(scale)]

print('Memory for lookup table: ', start_mem - mem_free())
print('Memory alloc: ', start_alloc - mem_alloc())
print()
    

# print('lookup ', lookup)

x = [ -22, -1, 0, 1, 2, 3, 4, 5, 9, 11, 13, 15, 16, 47, 444, 10266, 129933, 1939393, 2**31-1, 2**31, 2**44, 2**88, 2**101, 2**187 ]

for i in x:
    # if i == 0: pass
    # else: print('bisect_right', i, 'index ', bisect.bisect_right(x, i), 'bit_length ', bit_length(i))
    if i > lookup[-1]: print(i, 'is too big for lookup.')
    else: print('find ', i, 'bisect_right ', bisect.bisect_right(lookup, i), 'bit_length ', bit_length_alt(i))    
print()
for i in x:
    # if i == 0: pass
    # else: print('bisect_right', i, 'index ', bisect.bisect_right(x, i), 'bit_length ', bit_length(i))
    if i > lookup[-1]: print(i, 'is too big for lookup.')
    else: print('find ', i, 'bisect_left ', bisect.bisect_left(lookup, i), 'bit_length ', bit_length_alt(i))    
print()
for i in x:
    # if i == 0: pass
    # else: print('bisect_right', i, 'index ', bisect.bisect_right(x, i), 'bit_length ', bit_length(i))
    if i > lookup[-1]: print(i, 'is too big for lookup.')
    else: print('find ', i, 'bisect both ', bisect.bisect_left(lookup, i), bisect.bisect_right(lookup, i))    

    
    
    
