
from collections import namedtuple

import _thread

try:
    import fsinit
except ImportError:
    import tests.fsinit as fsinit
del(fsinit)

try:
	from vdict import VolatileDict, VolatileDictException, DELETED, RO, checkstats
except:
	from lib.vdict import VolatileDict, VolatileDictException, DELETED, RO, checkstats



if __name__=='__main__':

    nl = print

    nl()
    print('=== A test script for VolatileDict. ===')
    nl()

    try:
        vd = VolatileDict({'First':1, 'Second': 2})
    except VolatileDictException as e:
        print('Try creating with dict len=2: ', e )
    nl()

    vk = VolatileDict.fromkeys(['a','b','c'], 2)
    print("VD class method fromkeys(['a','b','c'], 2) - > ")
    print( vk )
    print()

    vd = VolatileDict([('One',1), ('Two', 2)])

    print('dir(vdict) ', dir(vd))
    nl()
    print('isinstance(vd,dict) ', isinstance(vd,dict))

    print('New VolatileDict')

    checkstats(vd)
    nl()

    print("Add key/values, like vdict['a'] = 1.")
    for k, v in zip(['a','b','c'], [1, 2, 3]):
        print('Add ', k, v)
        vd[k] = v
    nl()

    checkstats(vd)

    vd.reset()
    print('after reset, changed ', bin(vd.changed))
    nl()

    vd['c'] = 4
    vd['d'] = 7

    print("Set two key/values, one with new key.")
    checkstats(vd)
    nl()

    print('Reset changed')
    nl()
    vd.reset()

    print('Test __iter__, insert order should be preserved in mpy.')
    for k in iter(vd):
        print(k, end=" " )
    nl(), nl()

    print('vdict.items()')
    for k, v in vd.items():
        print( k, v, sep=' : ')
    nl()

    vu1 = { 'e': 23, 'f': 44, 'g': 22 }
    vu2 = [('d', 388), ('e',  133), ('f', 266), ('g', 733)]

    print('Testing update() ...')
    nl()
    print('Update from another dict')
    print('before   ', vd)
    vd.update(vu1)
    print('after 1  ', vd)
    print('Update from list of tuple pairs')
    vd.update(vu2)
    print('after 2  ', vd)
    nl()

    try:
        vd.update('big mistake !')
    except Exception as e:
        print('Update with error ', e)
    nl()

    checkstats(vd)

    print("reset('e') ")
    vd.reset('e')
    print('-> vkeys changed ', vd.keys_changed())
    nl()

    print('Fetch and reset single or list of keys')
    print('vkeys changed ', vd.keys_changed())
    print("fetch ['f', 'g'], returning items", vd.fetch(['f', 'g']))
    print('vkeys changed ', vd.keys_changed())
    print("fetch 'd', returning items", vd.fetch('d'))
    print('vkeys changed ', vd.keys_changed())
    nl()

    print('Using namedtuple DELETED as a value', DELETED)
    nl()
    vd['a'] = 4444
    vd['d'] = [ 1, 2, 3]
    vd['c'] = DELETED

    nl()
    print('### Read Only Test ###')
    nl()
    print('vd.read_only ', vd.read_only)
    print("vd.read_only.extend(['e','f', 'x'])")
    vd.read_only.extend(['e','f', 'x'])
    print('vd.read_only ', vd.read_only)
    nl()
    print("vd['f'] -> ", vd['f'])
    print("try: except: vd['f']=33")
    try:
        vd['f']=33
    except VolatileDictException as e:
        print(e)
    nl()
    print("'try: except: vd.pop('e')")
    try:
        vd.pop('e')
    except VolatileDictException as e:
        print(e)
    nl()
    print("'x' in vd ", 'x' in vd)
    print("try: except: del(vd['x'])")
    try:
        del(vd['x'])
    except VolatileDictException as e:
        print(e)

    nl()
    print("do first write to ro key 'x'")
    print("vd['x'] = 654")
    vd['x'] = 654
    print("vd['x'] ->", vd['x'])
    print("try: except: vd['x'] = 789")
    try:
        vd['x'] = 789
    except VolatileDictException as e:
        print(e)
    nl()

    print('Test vdict create with RO/red_only flag')
    dro = [('a', 1), RO('b', 2), ('c', 3), RO('d', 4 ), ('e', 5), RO( 'f', 6 )]
    print('kv list ', dro)
    vdro = VolatileDict(dro)
    print('vdict keys ', vdro.keys() )
    print('vdict read only ', vdro.read_only )
    nl()
    print('### End Read Only test ###')
    nl()

    print('vd using __str__')
    print(str(vd))
    nl()
    print("vd['c'] == DELETED ", vd['c'] == DELETED)
    nl()

    print("pop 'c' with returned value: ", vd.pop('c'))
    print("'c' in vdict: ", 'c' in vd)
    nl()
    try:
        print("Trying pop('x')")
        v = vd.pop('x')
    except Exception as e:
        print(e)
    nl()
    print('vkeys   ', vd.vkeys)
    print('changed ', bin(vd.changed))
    print("Trying del(vd['d']) using __delitem__ ")
    del(vd['d'])
    print("'d' in vdict    :", 'd' in vd)
    print('vkeys   ', vd.vkeys)
    print('changed ', bin(vd.changed))
    nl()

    print("'a' in vdict    :", 'a' in vd)
    print("'x' not in vdict:", 'x' not in vd )
    nl()

    print('len(vdict) ', len(vd))
    print("vdict.get('a')         ", vd.get('a'))
    print("vdict.get('xxx', None) ", vd.get('xxx', None))
    print('vdict.keys  ', vd.keys())
    print('vdict.values ', vd.values)
    nl()

    try:
        x = vd.popitem()
    except NotImplementedError:
        print('Error: popitem NotImplementedError')

    # print('str ', vd.__str__())    # not pretty, blows up mpy
    # print('repr ', vd.__repr__())  # not pretty, blows up mpy
    nl()

    print('del(vdict) ')
    nl()
    del(vd)

    try:
        x = vd.items()
    except:
        print("It's gone ... almost.")

    nl()

    vdvals = [ (k, i) for i, k, in enumerate(['a','b','c','d','e','f','g','h'])]

    print('Test for MicroPython, note key order of dict vs. OrderedDict')
    nl()
    print('kv tuple pairs          ', vdvals)
    print('dict(vdvals) Note order ', dict(vdvals))

    vd = VolatileDict(vdvals)
    nl()
    print('New VDict from kv-pairs')
    checkstats(vd)
    nl()

    print('VDict(vdvals)      ', vd)
    print('VDict.keys() ', vd.keys())
    print('VDict.items() ', vd.items())

    # print('VDict.__class__ ', vd.__class__)
    # print('VDict.__class__.__name__ ', vd.__class__.__name__)
    # print('VDict.__qualname__ ', vd.__qualname__)     # not Python 3.9

    nl()
    vx = vd.copy()
    print('Testing Copy, vd.copy() -> ', vx)
    nl()
    checkstats(vx)
    nl()
    print('Fetch changed values from new VDict')
    vals = vx.fetch(vx.keys_changed())
    print('values fetched ', vals)
    print("Pop 'f' -> ", vx.pop('f'))
    nl()
    print('New VDict')
    checkstats(vx)
    nl()
    print('Original VDict')
    checkstats(vd)
    nl()
    vd.clear()

    print('Original VDict cleared ')
    checkstats(vd)
    print('Len of new VDict: ', len(vx))
    nl()

    vx = dict(vdvals)

    MsgDef = namedtuple('MsgDef', [ 'message', 'comment'])
    msg1 = MsgDef('This is a test', 'what else ?')
    msg2 = MsgDef('This is also a test', '...etc !')

    print('get xxx            -> ', vx.get('xxx'))
    print('get xxx, not found -> ', vx.get('xxx', 'not found'))
    print('get with default      ', vx.get('xxx','message'))
    print('setdefault _msgdef     ', vx.setdefault('_msgdef', MsgDef))
    print('setdefault _message1  ', vx.setdefault('_message1', msg1))
    print('setdefault _message2  ', vx.setdefault('_message2', msg2))
    nl()
    for m in ['_msgdef', '_message1','_message2']: print(m ) # del(vx[m])    #  print(m) del(vx[m])
    print('get _message1 ', vx.get('_message1'))
    print('get _message2 ', vx.get('_message2'))
    print('get _msgdef   ', vx.get('_msgdef'))
    nl()
    rmsgdef = vx.get('_msgdef')
    print("vx.get('_msgdef') ",rmsgdef)
    rmsg = rmsgdef('testing', 'dynamic')
    print("rmsgdef('testing', 'dynamic')", rmsg)
    print("vx.get('xxx') ", vx.get('xxx'))
    print("vx.get('xxx',vx['_message1']) ", vx.get('xxx',vx['_message1']))
    nl()

    print('dict vx ', vx)
    print()

    print('isinstance(msg1, rmsgdef) ', isinstance(msg1, rmsgdef))
    print('dir msg1 ', dir(msg1))


    print('=== Test Locking  ===')
    
    import time

    print()
    print('dir(_thread): ', dir(_thread))
    print()

    vd = VolatileDict([( 'a', 3 ), ( 'b', 4 ), ( 'c', 7 )])
    dd = dict(vd.items())
    print()
    print('vdict:   ', vd)
    print()
    # print('dir(vdict): ')
    # print(dir(vd))
    # print()

    def vwrite(vdict, ll):

         print('in vwrite - ll.locked(): ', ll.locked())

         vdict['c'] = 444
         vdict['d'] = 5555

         print('in vwrite - ll.locked(): ', ll.locked())

         print('Updated vdict \n')

         # _thread.exit()
         return


    ll = vd.lock
    print('lock      ', ll)
    print('dir(lock) ', dir(ll))

    print('acquire()')
    
    # 
    ll.acquire()

    print('ll.locked(): ', ll.locked())

    vw_tuple = ( vd, ll )

    try:
        tident = _thread.start_new_thread(vwrite, vw_tuple)
        print('tident: ', tident)
    except Exception as e:
        print('Exception: ', e )
    finally:
        print('Back from start thread ')

    for k in vd.keys():
        print(f"vdict['{k}'] ", vd[k] )

    time.sleep(2)

    ll.release()

    print('ll,release(), ll.locked(): ', ll.locked())
    print()
    print('_thread.get_ident(): ', _thread.get_ident())
    print('_thread.stack_size:  ', _thread.stack_size())
    print()

    print('vdict: ', vd)
    print()
    # print('dict   ', dd)   # order in mpy is 'a', 'c', 'b'

