### Dumb structure time test, any memory leak problems ?


try:
    from gc import mem_free, mem_alloc, collect
    mem_free_avail = True
    start_mem = mem_free()
    start_alloc = mem_alloc()
    print('Start mem before import: ', start_mem)
    print('Start alloc before import: ', start_alloc)
    print
except:
    mem_free_avail = False

try:
    from time import time_ns as monotonic_ns
except:
    from time import monotonic_ns
    
from collections import namedtuple, OrderedDict

try:
    from utils import fix_paths
except:
    from dev.utils import fix_paths

fix_paths()


from liststore import ListStore, TupleStore
from tablestore import TableStore, TableDef, ColDef

from dev.vdict import VolatileDict

# from random import randint

if mem_free_avail:
    print('Mem use after import: ', start_mem - mem_free() )
    print('Increase mem alloc after import: ', mem_alloc() -start_alloc ) 

ntest = 100  
tscale = 1000000  # scaling ns to ms

starttotalt = monotonic_ns()



# UpperLOA = "ABCCDEFGHIJKLMNOPQRSTUVWXYZ"
# LowerLOA = "abcdefghijklmnopqrstuvwxyz"
UpperLOA = "ABCDEFGHIJKLMOPQ"
LowerLOA = "abcdefghijklmopq"
vlen = 5
Values = ['a'*vlen, 'b'*vlen, 'c'*vlen, 'd'*vlen, 'f'*vlen, 'g'*vlen, 'h'*vlen ]

keys = [ u+l for u in UpperLOA for l in LowerLOA ]
lpairs =[]

startt = monotonic_ns()



'''for i in range(len(keys)):  compreh. 5 x difference
    
    value = Values[i%len(Values)]
    lpairs.append((keys[i], value))'''
    
lpairs = [(keys[i], Values[i%len(Values)]) for i in range(len(keys))]
    

stopt = monotonic_ns()

print()

print('List build comp (ms): ', (stopt - startt)/tscale)
print('Scale is : ', len(lpairs))
print('Repeats = ', ntest)
print()

# Letters = namedtuple('Letters', [ 'upper', 'lower' ])

imax = 2**16


print('##### First Round ... build dict #####' )



startt = monotonic_ns()

for i in range(ntest):
    dd = {}
    for k, v in lpairs:
        dd[k] =  v  

        
stopt = monotonic_ns()
print()

print('dict len(dd): ', len(dd))
print('build dict with for k, v in lpairs loop (ms): ', (stopt - startt)/tscale)

if mem_free_avail:
    print('Mem use after dict build: ', start_mem - mem_free() )
print()

del(dd)

startt = monotonic_ns()

for i in range(ntest):
    dd = {}
    dd = dict(lpairs)
        
stopt = monotonic_ns()
print()

print('dict len(dd): ', len(dd))
print('build dict directly from dict(lpairs) (ms): ', (stopt - startt)/tscale)
print()
print("Note: should be faster than loop ('repeat' versus 'repeat x scale')," )
print('but is slower on micropython Pico v.21, about same on Nano ESP32 v.22.')
print('Compare to VDict, subclass of dict.' )
print()

print('##### build OrderedDict #####' )

del(dd)
if mem_free_avail: collect()



startt = monotonic_ns()

for i in range(ntest):
    dd = OrderedDict()
    for k, v in lpairs:
        dd[k] =  v  

        
stopt = monotonic_ns()
print()

print('Ordered Dict len(dd): ', len(dd))
print('Ordered Dict build (ms): ', (stopt - startt)/tscale)

if mem_free_avail:
    print('Mem use after Ordered Dict build: ', start_mem - mem_free() )
print()




print('##### OrderedDict rewrites #####' ) 


startt = monotonic_ns()

# use existing dd 
for i in range(ntest):
    for k, v in lpairs:
        dd[k] =  v 
        
stopt = monotonic_ns()

print('len(dd): ', len(dd))
print('Rewrites(ns): ', (stopt - startt)/tscale)
print()

del dd
if mem_free_avail: collect()

try:
    x = dd
    print('dd still there')
except:
    print('dd gone')
print()

print('##### Second Round ... append/extend list  #####' )



startt = monotonic_ns()

for i in range(ntest):
    klist = []
    klist.extend( lpairs )  # key  # ( l1, l2 ) $ reports 58944

        
stopt = monotonic_ns()


print('List Extend(ms): ', (stopt - startt)/tscale)
print()

klist = []

startt = monotonic_ns()

for i in range(ntest):
    klist = []
    for k, v in lpairs:
        klist.append( k )  # key  # ( l1, l2 ) $ reports 58944

        
stopt = monotonic_ns()



print('List Append(ms): ', (stopt - startt)/tscale)
print()




print('### List index() Function ###')
print()

startt = monotonic_ns()

for i in range(ntest):
    for key, value in lpairs:
        x = klist.index(key)
        # print(key, value, x )
        # key  # ( l1, l2 ) $ reports 58944
        # x = dd[key]  # key  # ( l1, l2 )  $ reports 111936
        
stopt = monotonic_ns()

print('List index() Function(ms): ', (stopt - startt)/tscale)
print()


del(klist)

if mem_free_avail:
    collect()
    print('Mem use after dict/klist del and collect: ', start_mem - mem_free() )



endtotalt = monotonic_ns()        

print()
print('##### Third Round ... ListStore  #####' )
print()


print('ListStore append lpairs in loop.')
startt = monotonic_ns()
# print('Start time(ns): ', startt )

# print(lpairs[-1])

for i in range(ntest):
        # print('Iter ', i , 'mem avail: ', mem_free())
    ls = ListStore(['key', 'value'])
     
    for k, v in lpairs:
        ls.append((k, v))  



stopt = monotonic_ns()


print('Append ListStore(ms): ', (stopt - startt)/tscale)
print('ls.length ', ls.length)
print('index ' , ls.index )
print()

del(ls)
if mem_free_avail: collect()

print('ListStore extend with lpairs.')
startt = monotonic_ns()

for i in range(ntest):
        # print('Iter ', i , 'mem avail: ', mem_free())
    ls = ListStore(['key', 'value'])
     
    ls.extend(lpairs)  



stopt = monotonic_ns()


print('Extend ListStore(ms): ', (stopt - startt)/tscale)
print('ls.length ', ls.length)
print('index ' , ls.index )
print()

print("### Index 'value' ###")
print()
startt = monotonic_ns()

for i in range(ntest):
    ls.index_attr('value')

stopt = monotonic_ns()
print("Index 'value' attr (ms): ", (stopt - startt)/tscale)
print()
print('ls.index.keys() ', ls.index)
keys = ls.index['value'].keys()

# print(keys)
# print(dir(keys))
# print('len(keys) ', len(keys))

print()
print("### Use list index['value'][key] for int mask and get rows ###")
print()
startt = monotonic_ns()
# print('Start time(ns): ', startt )
# print()

for i in range(ntest):
    for k in keys:
        bint = ls.index['value'][k]
        # print(bint)
        result = ls.get_rows(bint)
        # print(bint, result)

stopt = monotonic_ns()
print("Get index for value[k] and get_rows with index (ms): ", (stopt - startt)/tscale)
print()        
        



def find( val, inlist, start=0 ):

    try:
        i = inlist.index(val, start)
    except ValueError as ve:
        i = -1
        
    return i

def find_all ( val, inlist ):

    il = []
    start = 0
    i = 0

    while i > -1:
        try:
            i = inlist.index(val, start)
            il.append(i)
            start = i + 1
        except ValueError as ve:
            i = -1

    return il


keys = ls.get_column('key')
print()
print("### Use find() to get slot for 'key' ###")
print('using keys, len = ', len(keys))
print()
startt = monotonic_ns()

for i in range(ntest):
    for k in keys:
        xt = find(k, keys )
        # print( k, xt)

stopt = monotonic_ns()
print("Get slot for unqiue key in ls.key (ms): ", (stopt - startt)/tscale)
print()  

print()
print("### Use find_all() to get slots for 'value' ###")
values = keys = ls.get_column('value')
vset = set(values)
print('using vset ', vset)
print()
startt = monotonic_ns()




for i in range(ntest):
    for v in vset:
        xt = find_all(v, values )
        # print( v, xt )

stopt = monotonic_ns()
print("Get slots for duplicate values in ls.value (ms): ", (stopt - startt)/tscale)
print() 
      


print('##### Fourth Round ... TupleStore  #####' )

startt = monotonic_ns()
print('Start time(ns): ', startt )

for i in range(ntest):
    ls = TupleStore(nt_name='TestTuple', column_defs=['key', 'value'])
    ls.extend(lpairs)

stopt = monotonic_ns()


print('Extend TupleStore(ms): ', (stopt - startt)/tscale)
print('index ' , ls.index )
print()

print('##### Fifth Round ... TablesStore  #####' )

tstore_def = TableDef(tname = 'Test', filename = 'testing111', unique=['key'],
					 col_defs = [ColDef(cname='key', default=None, ptype=str),
								 ColDef(cname='value', default=0, ptype=str)])

startt = monotonic_ns()
print('Start time(ns): ', startt )

for i in range(ntest):
    ts = TableStore(tstore_def)
    ts.extend(lpairs)

stopt = monotonic_ns()


print('Extend TableStore(ms): ', (stopt - startt)/tscale)
print('index ' , ls.index )
print()




print('##### Sixth Round ... VolatileDict  #####' )

startt = monotonic_ns()
print('Start time(ns): ', startt )
print()

for i in range(ntest):
    vdict = VolatileDict(lpairs)

stopt = monotonic_ns()

print('VolatileDict directly from tuple pairs (ms): ', (stopt - startt)/tscale)
print('len(vdict) ', len(vdict))
print()

startt = monotonic_ns()


for i in range(ntest):
    vdict = VolatileDict()
    for k, v in lpairs:
        vdict[k] = v

stopt = monotonic_ns()


print('VolatileDict from vdict[k] = v in lpairs (ms): ', (stopt - startt)/tscale)
print('len(vdict) ', len(vdict))

endtotalt = monotonic_ns()  

print()
print('Result')
print('Time(ms): ', (endtotalt - starttotalt)/tscale)

# print('x ', x)
# print('klist[-1]  ', klist[-1])

if mem_free_avail:
    print('End mem free: ', mem_free() )
    print('mem use: ',  start_mem - mem_free())
    print('increase mem alloc : ',  mem_alloc() - start_alloc)
    # collect()
    # print('mem use(after gc): ',  start_mem - mem_free())
    print()
    # print(dd)
