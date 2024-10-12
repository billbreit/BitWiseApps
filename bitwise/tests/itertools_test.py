
try:
    from micropython import const
except:
    const = lambda x:x

try:
    import fsinit
except:
    import tests.fsinit as fsinit
del(fsinit)

try:
    import gentools as g
except:
    import lib.gentools as g

nl = print


if __name__ == '__main__':

    ch = g.chain([1,2,3],[4,5,6])
    print("g.chain([1,2,3],[4,5,6]) ", ch )
    nl()

    print('groupby list((k,g)) ', [list((k,g)) for k, g in g.groupby('AAAABBBCCD')], '-> AAAA BBB CC D')
    nl()
    print('groupby list(g) ', [list(g) for k, g in g.groupby('AAAABBBCCD')], '-> AAAA BBB CC D') 
    nl()

    print('accumulate ', [ n for n in g.accumulate([1,2,3,4,5], g.mul, initial=1)])
    nl()

    ilist = [1,2,3,4,5,6,7,8]

    tt = g.tee(ilist, 4)

    for t in tt:
        print(list(t))
        
    print()



     
    la = [1,4,5, 6,3,8]
    lb = [ 2, 4 ,6, 8, 10 ]

    dw = g.dropwhile(lambda x: x<4, la)
    tw = g.takewhile(lambda x: x<4, la)

    print('dir(dropwhile) ', dir(dw))
    print()

    print('list(dw) x<4 ', list(dw))
    print('list(tw) x<4 ', list(tw))

    print('filtertrue x<5 ', *g.filtertrue(lambda x: x<5, g.chain(la, lb)))
    print('filterfalse x<5 ', *g.filterfalse(lambda x: x<5, g.chain(la, lb)))
    print()

    print('flatten')
    print()
    xg = ( x for x in [ 1, 2, 3 ])

    items = [1, 2, ['hello', b'world'], xg, ( 'able', 'bug', 'clat' ), [3, 4, {'five':5, 'six':6}, {'five':5, 'six':6}.items()], 8]

    # Produces 1 2 3 4 5 6 7 8
    print('loop flatten ')
    for x in g.flatten(items):
        print(x, end=" -> " )
    print(end='\n\n')


    print('list flatten')
    x = g.flatten(items)
    print(list(x))

    print('dict.items() ', {'five':5, 'six':6}.items())

    print()
    
    print('testing islice() ')
    print(list(g.islice('ABCDEFG', 2))) # -> A B
    print(list(g.islice('ABCDEFG', 2, 4))) # -> C D
    print(list(g.islice('ABCDEFG', 2, None))) # -> C D E F G
    print(list(g.islice('ABCDEFG', 0, None, 2))) # -> A C E G



    # from stackoverlfow.com/questions /... /python-generator-is-too-slow-to-use

    #import timeit
    
    try:
        from utils import timer
    except:
        from dev.utils import timer
    


    n = 100

    # testlist = [ 'hello' ] * n

    testlist = [ 'hello'+str(i) for i in range(n)]

    print()
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

    listcomp is about 2x faster, but gen is about same ?

    RPZero

    Timed 'test_list_comp' repeated 1000 times: 746.316768 msecs.
    Timed 'test_genexp' repeated 1000 times: 1183.546287 msecs.
    Timed 'test_genfunc' repeated 1000 times: 1157.326434 msecs.
    """



