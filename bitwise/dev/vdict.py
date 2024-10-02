"""

module:     vdict
version:    v0.4.4
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

Volatile Dictionary - tracks keys of changed items for notification/synching between
    peer [writer -> reader] processes, possibly two-way processes [peer <-> peer].
    
    - generally add/modify only, usually all keys will created before using dict,
      such as [one writer -> many readers].  

    - dict.__del__ and dict.pop are supported, (not yet with  with 'row locking'),
      which guarantees validity of shared references and access masks on the
      row/dict key level.  popitem not supported, not thread-safe without lock.
      
    -  Use k-v tuple pairs to maintain order of entry, OrderedDict equivalent. 
    
    - Can be used like OrderedDict where none, some low-memory upython builds.
      Implements dict.update - may not be supported on small builds.
    
    - Note: micropython base class inheritence is much improved, but it won't run 
      on old versions of CircuitPython, try OrderedDict.  However,
      OrderedDict is still not the default on many mpy builds. 

    Works with Python v3.9 and micropython v1.20.0 on a RP Pico
    Does not work with Circuit Python, can't subclass dict without
    recursive crash.
    
    Some of the design limitations are artificial.  New writer->reader relations can be
    added and deleted at will, but it's not clear why do it under most 'tightly coupled'
    usage scenarios.  Some sort of namespacing and 'namedspace merge' might be more useful.
    
"""


# ODict may not be availible on limited micropython build,
# dict on mpy is signifcantly faster than ODict.


from collections import namedtuple

try:
    from bitlogic import bit_indexes, power2, bit_length, bit_remove
except:
    from dev.bitlogic import bit_indexes, power2, bit_length, bit_remove



nl = print

DELETED = namedtuple('DELETED',[])      # as class
# DELETED = namedtuple('DELETED',[])()  # as instance, not class

class VolatileDictException(Exception):
    pass

""" mpy v1.21.0 dir(dict)
['__class__', '__delitem__', '__getitem__', '__name__', '__setitem__',
'clear', 'copy', 'get', 'items', 'keys', 'pop', 'popitem', 'setdefault',
'update', 'values', '__bases__', '__dict__', 'fromkeys']


"""


class VolatileDict(dict):   # faster, OrderedDict may not be availible
    """ Volatile Dictionary, tracks keys of changed items for notification/synching.
    
        - add/modify only, generally all keys will created before using dict
        - No del, pop, popitem, whcih guarantees validity of all externally shared
          access masks.  Not thread-safe without lock.
        - implements update - works in Python, but not upython
        - Can be used like OrderedDict where none, some low-memory upython builds.
        - Use k-v tuple pairs to maintain order of entry. 
        
        - Note: micropython base class inheritence is much improved, but it won't run 
          on old versions of CircuitPython, Try OrderedDict, however OrderedDict
          is often not availible on old mpy builds. 
    """
    
    def __init__( self, *args, **kwargs ):
        
        super().__init__(*args, **kwargs)
        self.vkeys = []    # ensure insert order, OrderedDict may not be avail.
        self.changed = 0
            
        # print('len(args), args[0] ', len(args), args[0])   
        
        if len(args) > 0:
            if isinstance(args[0], dict):   # preserve insert order
                raise  VolatileDictException(f'Init Error: can only create vdict from tuple pairs.')
            self.vkeys = [ kv[0] for kv in args[0] ]
            self.changed |= power2(len(args[0]))-1
        
    def __setitem__(self, key, value ):
        """ Track changed items """

        super().__setitem__(key, value)
        if key not in self.vkeys:
            self.vkeys.append(key)  # ensure insert order
        self.changed |= power2(self.vkeys.index(key))
        

    def __delitem__(self, key):
        """ Not useful for volatile dict, set value to None or DELETED"""
        
        super().__delitem__(key)
        slot = self.vkeys.index(key)
        self.vkeys.remove(key)
        self.changed = bit_remove(self.changed, slot )
        
    def __iter__(self):
        
        for k in self.vkeys: yield k
        
    def __str__(self):
        
        ss = self.__class__.__name__ + '({'
        kvs = [ repr(k) + ': ' + repr(v)  for k, v in self.items()]
        ss += ', '.join(kvs)
        ss += '})'
        return ss

    def __repr__(self):
        
        ss = self.__class__.__name__ + '(['
        kvs = [ '(' + repr(k) + ', ' + repr(v) + ')'  for k, v in self.items()]
        ss += ', '.join(kvs)
        ss += '])'
        return ss
     
    @classmethod
    def fromkeys(self, keys:list, value=None ) -> 'VolatileDict':
    
        # kvtuples = [ ( key, value ) for key in keys ]
        return VolatileDict([( key, value ) for key in keys ])
        
    def copy(self)  -> 'VolatileDict':
    
        vd = VolatileDict(self.items())
        vd.changed = self.changed
        vd.vkeys = self.vkeys[:]
        
        return vd
        
    def clear(self):
    
        super().clear()
        self.changed = 0
        self.vkeys = []       
      
    def items(self) ->list[tuple]:
        "Ensures insert order, for mpython" 
        return [(k, self[k]) for k in self.vkeys]
    
    def keys(self) -> list:
        return self.vkeys
        # return super().keys()  # not ordered in mpy, useful debugging
    
    @property
    def values(self) -> list:
        """Maintaining order"""
        return [self[k] for k in self.vkeys]
        
    def setdefault(self, key, value=None ):
        """If key not in dict, add with default. Then return current value."""
    
        if key not in self.keys():
            self.__setitem__( key, value )

        return self[key]
    
    def pop(self, key) -> 'value':
        """ Can be used, but not really useful for complex reader/writer
           relationships.  Better set value to DELETED"""
        if key not in self:
            raise  VolatileDictException(f"Key Pop Error: key '{key}' not found. No delete.")
        
        item = super().pop(key)
        slot = self.vkeys.index(key)
        self.vkeys.remove(key)
        self.changed = bit_remove(self.changed, slot)
        
        return item

    def popitem(self):
        """ Not useful for volatile dict, too unpredictable for vdict usage scenario,
            set value to None or DELETED"""
        raise NotImplementedError
    
     
    def update(self, dictorlist ):
        """Generally run once during dict lifespan.  If dictorlist is mpy
           dict, key order is not guaranteed."""
        
        if isinstance(dictorlist, dict) and len(dictorlist)>0 :
            for k, v in dictorlist.items():
                self.__setitem__(k, v)
        elif isinstance(dictorlist, (list, tuple)):
            for k, v in dictorlist:
                self.__setitem__(k, v) 
        else:
            raise  VolatileDictException(f"Update Error: update failed for input '{dictorlist}'.")
        
        
    def ischanged(self) -> bool:
        return self.changed != 0
        
    def reset(self, key=None):
        """ If no key, set changed to 0. If key, AND of NOT slot index into changed """
    
        # print('in reset ', key, self.vkeys, self.keys())
        
        if key is not None and key not in self.vkeys:
            raise  VolatileDictException(f"Key Reset Error: key '{key}' not found.")
            
        if key:
            self.changed &= ~power2(self.vkeys.index(key))
        else:
            self.changed = 0
        
    def keys_changed(self) -> list:
    
        # print('changed ', bin(self.changed), bit_indexes(self.changed) )
        
        return [self.vkeys[i] for i in bit_indexes(self.changed)]
        
    def fetch(self, keylist:list=None ) -> list['value']:
        """ Get values for list of keys, reset changed bit and
             return list of items """ 
        
        if not keylist:
            return []
            
        if not isinstance(keylist,(list, tuple)):
            keylist = [keylist]
  
        itemlist = [ self[key] for key in keylist ]
                            
        for key in keylist:
            self.reset(key)
        
        return itemlist
        
        
 
def checkstats(vdict):
    print('Stats')
    print('vdict:        ', vdict)
    print('vdict len:    ', len(vdict))
    print('is changed:   ', vdict.ischanged())
    print('changed mask: ', bin(vdict.changed))
    print('vkeys:        ', vdict.vkeys)
    print('vkeys changed:', vdict.keys_changed())
    nl()


if __name__=='__main__':


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
    print('vdict.items ', vd.values)
    nl()

    """
    print('Exceptions')
    nl()
    try:
        del vd['a']
    except NotImplementedError:
        print('Error: delete NotImplementedError')

    try:
        x = vd.pop('a')
    except NotImplementedError:
        print('Error: pop NotImplementedError')
    """
    
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
    """
    nl()
    vx.clear()
    
    print('New VDict cleared ')
    checkstats(vx)
    """
    
    vx = dict(vdvals)
    
    MsgDef = namedtuple('MsgDef', [ 'message', 'comment'])
    msg1 = MsgDef('This is a test', 'what else ?')
    msg2 = MsgDef('This is also a test', '...etc !')   

    print('get xxx            -> ', vx.get('xxx'))
    print('get xxx, not found -> ', vx.get('xxx', 'not found')) 
    print('get with default      ', vx.get('xxx','message'))
    print('setdefault msgdef     ', vx.setdefault('_msgdef', MsgDef))
    print('setdefault message1  ', vx.setdefault('_message1', msg1))
    print('setdefault message2  ', vx.setdefault('_message2', msg2))
    for m in ['_msgdef', '_message1','_message2']: print(m ) # del(vx[m])    #  print(m) del(vx[m])
    print('get message1 ', vx.get('_message1')) 
    print('get message2 ', vx.get('_message2'))
    print('get msgdef   ', vx.get('_msgdef'))
    rmsgdef = vx.get('_msgdef')
    print(rmsgdef)
    rmsg = rmsgdef('testing', 'dynamic')
    print('use msgdef       ', rmsg)
    print('get xxx          ', vx.get('xxx'))  
    print('get with default ', vx.get('xxx',vx['_message1']))
    
    
    # checkstats(vx)
    
    print('dict vx ', vx)
    
    print()
        
    print('instance ', isinstance(msg1, rmsgdef))
    print('dir instance msg1 ', dir(msg1))
    
    
    print()
    print('Further ...')
    vz = VolatileDict([('a', 1),('b',2),('c',3)])
    print('vz ', vz )
    print()
    
    print(dir(vz))
 
    
    
    

    

        

