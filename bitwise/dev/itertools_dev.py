""" A full set of itertools functions, copped from Python 12 itertools
documentation ("roughly equivalent to"), for micropython compatibility.
Also good examples of generator constructs. """

try:
    from micropython import const
except:
    const = lambda x:x
    

nl = print

#from operator

def add(a, b):
    "Same as a + b."
    return a + b
    
def mul(a, b):
    "Same as a * b."
    return a * b

def accumulate(iterable, function=add, *, initial=None):

    'Return running totals'
    # accumulate([1,2,3,4,5]) → 1 3 6 10 15
    # accumulate([1,2,3,4,5], initial=100) → 100 101 103 106 110 115
    # accumulate([1,2,3,4,5], operator.mul) → 1 2 6 24 120

    iterator = iter(iterable)
    total = initial
    if initial is None:
        try:
            total = next(iterator)
        except StopIteration:
            return  # None

    yield total
    for element in iterator:
        total = function(total, element)
        yield total

def batched(iterable, n):

    # batched('ABCDEFG', 3) → ABC DEF G
    
    if n < 1:
        raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        yield batch

def chain(*iterables):

    # chain('ABC', 'DEF') → A B C D E F
    
    for iterable in iterables:
        yield from iterable

def from_iterable(iterables):

    # chain.from_iterable(['ABC', 'DEF']) → A B C D E F
    
    for iterable in iterables:
        yield from iterable
        
def isiterable(it):
    """Needed.  Mpy doesn't implement __iter__ for list, etc."""

    try:
        x = iter(it)
    except:
        return False
    else:
        return True

        
def flatten(items, ignore_types=(str, bytes, dict)):
    for x in items:
        if isiterable(x) and not isinstance(x, ignore_types):
            yield from flatten(x)
        else:
            yield x


def compress(data, selectors):

    # compress('ABCDEF', [1,0,1,0,1,1]) → A C E F
    
    return (datum for datum, selector in zip(data, selectors) if selector)

def count(start=0, step=1):

    # count(10) → 10 11 12 13 14 ...
    # count(2.5, 0.5) → 2.5 3.0 3.5 ...
    
    n = start
    while True:
        yield n
        n += step

def cycle(iterable):

    # cycle('ABCD') → A B C D A B C D A B C D ...
    
    saved = []
    for element in iterable:
        yield element
        saved.append(element)
    while saved:
        for element in saved:
            yield element

def dropwhile(predicate, iterable):

    # like drop until condition is False, trigger to on
    # dropwhile(lambda x: x<5, [1,4,6,3,8]) → 6 3 8

    iterator = iter(iterable)
    for x in iterator:
        if not predicate(x):
            yield x
            break

    for x in iterator:
        yield x
        

def takewhile(predicate, iterable):

    # like accept until condition is False, trigger to off
    # takewhile(lambda x: x<5, [1,4,6,3,8]) → 1 4
    
    for x in iterable:
        if not predicate(x):
            break
        yield x

def filterfalse(predicate, iterable):

    # drop whenever condition is False
    # filterfalse(lambda x: x<5, [1,4,6,3,8]) → 6 8
    
    if predicate is None:
        predicate = bool
    for x in iterable:
        if not predicate(x):
            yield x
            
def filtertrue(predicate, iterable):

    # drop whenever condition is True
    # filtertrue(lambda x: x<5, [1,4,6,3,8]) → 1, 4, 3
    
    if predicate is None:
        predicate = bool
    for x in iterable:
        if predicate(x):
            yield x

def groupby(iterable, key=None):

    # [k for k, g in groupby('AAAABBBCCDAABBB')] → A B C D A B
    # [list(g) for k, g in groupby('AAAABBBCCD')] → AAAA BBB CC D

    keyfunc = (lambda x: x) if key is None else key
    iterator = iter(iterable)
    exhausted = False

    def _grouper(target_key):
        nonlocal curr_value, curr_key, exhausted
        yield curr_value
        for curr_value in iterator:
            curr_key = keyfunc(curr_value)
            if curr_key != target_key:
                return
            yield curr_value
        exhausted = True

    try:
        curr_value = next(iterator)
    except StopIteration:
        return
    curr_key = keyfunc(curr_value)

    while not exhausted:
        target_key = curr_key
        curr_group = _grouper(target_key)
        yield curr_key, curr_group
        if curr_key == target_key:
            for _ in curr_group:
                pass

# def islice(iterable, *args):
def islice(iterable, istart=None, istop=None, istep=None):

    # islice('ABCDEFG', 2) → A B
    # islice('ABCDEFG', 2, 4) → C D
    # islice('ABCDEFG', 2, None) → C D E F G
    # islice('ABCDEFG', 0, None, 2) → A C E G

    """
    s = slice(*args)  ## not on mpy !!!

    start = 0 if s.start is None else s.start
    stop = s.stop
    step = 1 if s.step is None else s.step
    if start < 0 or (stop is not None and stop < 0) or step <= 0:
        raise ValueError
    """

    start = 0 if istart is None else istart
    stop = istop
    step = 1 if istep is None else istep
    if start < 0 or (stop is not None and stop < 0) or step <= 0:
        raise ValueError

    indices = count() if stop is None else range(max(start, stop))
    next_i = start
    for i, element in zip(indices, iterable):
        if i == next_i:
            yield element
            next_i += step

def pairwise(iterable):

    # pairwise('ABCDEFG') → AB BC CD DE EF FG
    
    iterator = iter(iterable)
    a = next(iterator, None)
    for b in iterator:
        yield a, b
        a = b
        
def combinations(iterable, r):

    # combinations('ABCD', 2) → AB AC AD BC BD CD
    # combinations(range(4), 3) → 012 013 023 123

    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))

    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)

def combinations_with_replacement(iterable, r):

    # combinations_with_replacement('ABC', 2) → AA AB AC BB BC CC

    pool = tuple(iterable)
    n = len(pool)
    if not n and r:
        return
    indices = [0] * r

    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                break
        else:
            return
        indices[i:] = [indices[i] + 1] * (r - i)
        yield tuple(pool[i] for i in indices)


def permutations(iterable, r=None):

    # permutations('ABCD', 2) → AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) → 012 021 102 120 201 210

    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return

    indices = list(range(n))
    cycles = list(range(n, n-r, -1))
    yield tuple(pool[i] for i in indices[:r])

    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return

def product(*iterables, repeat=1):

    # Like cartesian product 
    # product('ABCD', 'xy') → Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) → 000 001 010 011 100 101 110 111

    pools = [tuple(pool) for pool in iterables] * repeat

    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]

    for prod in result:
        yield tuple(prod)

def repeat(obj, times=None):

    # repeat(10, 3) → 10 10 10
    
    if times is None:
        while True:
            yield obj
    else:
        for i in range(times):
            yield obj

def starmap(function, iterable):

    # starmap(pow, [(2,5), (3,2), (10,3)]) → 32 9 1000
    
    for args in iterable:
        yield function(*args)


def tee(iterable, n=2):
    """Hmmm ..."""

    iterator = iter(iterable)
    shared_link = [None, None]
    return tuple(_tee(iterator, shared_link) for _ in range(n))

def _tee(iterator, link):

    try:
        print('in _tt ', iterator, link)
        while True:
            if link[1] is None:
                link[0] = next(iterator)
                link[1] = [None, None]
            value, link = link
            yield value
    except StopIteration:
        return

def zip_longest(*iterables, fillvalue=None):

    # zip_longest('ABCD', 'xy', fillvalue='-') → Ax By C- D-

    iterators = list(map(iter, iterables))
    num_active = len(iterators)
    if not num_active:
        return

    while True:
        values = []
        for i, iterator in enumerate(iterators):
            try:
                value = next(iterator)
            except StopIteration:
                num_active -= 1
                if not num_active:
                    return
                iterators[i] = repeat(fillvalue)
                value = fillvalue
            values.append(value)
        yield tuple(values)



if __name__ == '__main__':

    ch = chain([1,2,3],[4,5,6])
    print( [i for i in ch] )
    nl()

    print('groupby ', [list((k,g)) for k, g in groupby('AAAABBBCCD')], '-> AAAA BBB CC D') 
    print('groupby ', [list(g) for k, g in groupby('AAAABBBCCD')], '-> AAAA BBB CC D') 
    nl()

    print('accumulate ', [ n for n in accumulate([1,2,3,4,5], mul, initial=1)])
    nl()

    ilist = [1,2,3,4,5,6,7,8]

    tt = tee(ilist, 4)

    for t in tt:
        print(list(t))
        
    print()


    # from stackoverlfow.com/questions /... /python-generator-is-too-slow-to-use

    #import timeit
    try:
        from utils import timer
    except:
        from dev.utils import timer


    n = 100

    # testlist = [ 'hello' ] * n

    testlist = [ 'hello'+str(i) for i in range(n)]

    print('testlist ', testlist[99], len(testlist))
    print()

    def test_list_comp():
        # return [x for x in range(n)]
        return [x for x in testlist]
        
    def test_genexp():
        # return list(x for x in range(n))
        return list(x for x in testlist)

    def mygen(tlist):
        # for x in range(n):
        for x in tlist:
            yield x

    def test_genfunc():
        return list(mygen(testlist))

    for fname in [test_list_comp, test_genexp, test_genfunc]:
        result = timer(fname, repeat= n)()
        # result = timeit.timeit("fun()", "from __main__ import {} as fun".format(fname), number=1000)
        # print("{} : {}".format(fname.__name__, result))
        
    del(testlist)
    del(result)
     
    la = [1,4,5, 6,3,8]
    lb = [ 2, 4 ,6, 8, 10 ]

    dw = dropwhile(lambda x: x<4, la)
    tw = takewhile(lambda x: x<4, la)

    print('dir(dropwhile) ', dir(dw))
    print()

    print('list(dw) x<4 ', list(dw))
    print('list(tw) x<4 ', list(tw))

    print('filtertrue x<5 ', *filtertrue(lambda x: x<5, chain(la, lb)))
    print('filterfalse x<5 ', *filterfalse(lambda x: x<5, chain(la, lb)))
    print()

    print('flatten')
    print()
    g = ( x for x in [ 1, 2, 3 ])

    items = [1, 2, ['hello', b'world'], g, ( 'able', 'bug', 'clat' ), [3, 4, {'five':5, 'six':6}, {'five':5, 'six':6}.items()], 8]

    # Produces 1 2 3 4 5 6 7 8
    print('loop flatten ')
    for x in flatten(items):
        print(x, end=" " )
    print(end='\n\n')


    print('list flatten')
    x = flatten(items)
    print(list(x))

    print({'five':5, 'six':6}.items())

    print()
    
    print('testing islice() ')
    print(list(islice('ABCDEFG', 2))) # -> A B
    print(list(islice('ABCDEFG', 2, 4))) # -> C D
    print(list(islice('ABCDEFG', 2, None))) # -> C D E F G
    print(list(islice('ABCDEFG', 0, None, 2))) # -> A C E G



        

    """
    Here (py 2.7.x on a 5+ years old standard desktop) I get the following results:

    repeat = 10000

    test_list_comp : 0.254354953766
    test_genexp : 0.401108026505
    test_genfunc : 0.403750896454

    P400 py3.9:
    range(1000)
    test_list_comp : 0.64592200005427
    test_genexp : 1.353643943904899
    test_genfunc : 1.0990640410454944

    ['hello'] * 1000
    test_list_comp : 0.4856949069071561
    test_genexp : 0.9395720469765365
    test_genfunc : 0.9503267400432378

    ['hello'+str(i) for 1000 ]
    test_list_comp : 0.49218665109947324
    test_genexp : 0.9859581419732422
    test_genfunc : 0.9877844229340553

    Timed 'test_list_comp' repeated 1000 times: 68.031389 msecs.
    Timed 'test_genexp' repeated 1000 times: 109.760918 msecs.
    Timed 'test_genfunc' repeated 1000 times: 109.364756 msecs.



    RP Pico:  repeat = 1000
    ['hello'+str(i) for 1000 ]
    Timed 'test_list_comp' repeated 1000 times: 4719.037 msecs.
    Timed 'test_genexp' repeated 1000 times: 8726.147 msecs.
    Timed 'test_genfunc' repeated 1000 times: 8782.274 msecs.

    Arduino Nano ESP32(v1.22):  repeat = 1000
    ['hello'+str(i) for 1000 ]
    Timed 'test_list_comp' repeated 1000 times: 2479.212 msecs.
    Timed 'test_genexp' repeated 1000 times: 8009.604 msecs.
    Timed 'test_genfunc' repeated 1000 times: 8012.377 msecs.

    listcomp is 2x faster, but gen is about same ?

    RPZero

    Timed 'test_list_comp' repeated 1000 times: 746.316768 msecs.
    Timed 'test_genexp' repeated 1000 times: 1183.546287 msecs.
    Timed 'test_genfunc' repeated 1000 times: 1157.326434 msecs.



    """

    print()
    print("from lib  import fsutils and so on ...")
    print()




    def fix_parent():

        import os, sys 
               
        cd = os.getcwd()
        print('cwd ', cd) 
        
        print('sys.path ' , sys.path)
        print()
        
        if '\\' in cd:  
            pathsep = '\\'  # windows
        else:
            pathsep = '/'  # linux

        parentdir = pathsep.join(cd.split(pathsep)[:-1])      
     
        if parentdir not in sys.path:   # python,
            sys.path.append(parentdir)
            
        print('sys.path ',  sys.path)
        print(' os.getcwd() ', os.getcwd())
        print()
        
        # return
        
    # fix_parent()
    
    print()

    """
    import os, sys
    if sys.implementation.name == 'micropython':
        print('os.pwd() ', os.getcwd())
        os.chdir('/dev')
        print('os.pwd() ', os.getcwd())
    else:
        print('not micropython, os.pwd() ', os.getcwd())
    print()
    """
    
    """
    print('importing init ')
    import init
    print(init)
    print()
    """
        
    # fix_parent()
    #from lib import const   # fix_paths  # npt Py3.9, not mod named lib
    # from .lib import const   # fix_paths  # npt Py3.9, not mod named lib
    # from lib.fsutils import fix_paths  # mpy /lib in path, not python
    # from __init__ import const   # works with Py3.9, not mpy
    # from lib import const   # fix_paths   # not Py3.9
    # import fix_paths  #  not Py3.9
    # from . import const  # mpy no rel imp   # not Py3.9
    # import *   # not Py3.9
    # from . import *   # mpy no rel imp,  not Py3.9
    # from . import const  # not Py3.9   # relative import no known parent
    # from dev import const # working mpy, working Py3.9 with fix parent
    # from . import const
    # import const

    """
    ll = locals().copy()
    
    print(type(ll))
    
    print('locals')
    for k, v in ll.items():
        print(k, v)
    """

    x = const(3)
    print(x)



















