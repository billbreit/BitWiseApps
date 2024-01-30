""" Works with Python v3.9 and micropython v1.20.0 on a RP Pico
    Does not work with Circuit Python, can't subclass dict without
    recursive crash."""

# from collections import OrderedDict
# if availible on limited micropython build, dict might be slightly faster.

from collections import namedtuple

try:
    from collections import OrderedDict
    odict_avail = True
except:
    odict_avail = False

try:
    from utils import fix_paths
except:
    from dev.utils import fix_paths
fix_paths()

from dev.bitlogic import bit_indexes

nl = print

DELETED = namedtuple('DELETED', [] )

# class VolatileDict(OrderedDict):
class VolatileDict(dict):   # faster, OrderedDict may not be availible
    """ Volatile Dictionary, tracks keys of changed items for notification/synching.
    
        - add/modify only, generally all keys will created before using dict
        - No del, pop, popitem, whcih guarantees validity of all externally shared
          access masks.  Not thread-safe without lock.
        - implements update - works in Python, but not upython
        - Can be used like OrderedDict where none, some low-memory upython builds.
        
        - Note: micropython base class inheritence is much improved, but it won't run 
          on old versions of CircuitPython, try OrderedDict.  However,
          OrderedDict is still not the default on many mpy builds. 
    """
    
    def __init__( self, *args, **kwargs ):
        super().__init__(*args, **kwargs)
        self.changed = 0
        self.vkeys = []
        
    def __setitem__(self, key, value ):
        """ Track changed items """

        super().__setitem__(key, value)
        if key not in self.vkeys:
            self.vkeys.append(key)
        self.changed |= pow(2, self.vkeys.index(key))
     
    def __delitem__(self, item):
        """ Not useful for volatile dict, set value to None or DELETED"""
        raise NotImplementedError
    
    def pop(self, key):
        """ Not useful for volatile dict, set value to None or DELETED"""
        raise NotImplementedError
    
    def popitem(self):
        """ Not useful for volatile dict, set value to None or DELETED"""
        raise NotImplementedError
  
    def update(self, otherdict):
        """Simple ( and slow ) implementation for upython by forcing __setitem__ """
        
        for k, v in otherdict.items():
            vd[k] = v
        
    def ischanged(self):
        return self.changed != 0
        
    def reset(self, key=None):
        if key:
            self.changed &= ~pow(2, self.vkeys.index(key))
        else:
            self.changed = 0
        
    def keys_changed(self):
        
        ichanged = bit_indexes(self.changed)

        kchanged = [self.vkeys[i] for i in ichanged]
                
        return kchanged
        
    def fetch(self, keylist=None ):
        """ Get list of key, reset and return list of items """ 
        
        if not keylist: return []
            
        if isinstance(keylist, str): keylist = [keylist]
  
        itemlist = [ self[key] for key in keylist ]
                            
        for key in keylist: self.reset(key)
        
        return itemlist
    
    def items(self):
        "Ensures insert order, for mpython" 
        return [(k, self[k]) for k in self.vkeys]
    
    @property
    def keys(self):
        return self.vkeys
    
    @property
    def values(self):
        """Maintaining order"""
        return [self[k] for k in self.vkeys]


if __name__=='__main__':


    
    nl()
    print('A small test script for VolatileDict.')
    nl()
    
    vd = VolatileDict()
    
    print('dir(vdict) ', dir(vd))
    nl()
    print('isinstance(vd,dict) ', isinstance(vd,dict))
    if odict_avail:
        print('isinstance(vd,OrderedDict) ', isinstance(vd,OrderedDict)) 
    else:
        print('OrderedDict not avail')
    nl()
    
    print('New empty VolatileDict')
    def checkstats(vdict):
        print('Stats')
        print('vdict: ',  vdict)
        print('is changed ? ', vdict.ischanged())
        print('changed mask', bin(vdict.changed))
        print('vkeys ', vdict.vkeys)
        print('vkeys changed ', vdict.keys_changed())
        nl()
        
        
    # print(dir(vd))
    checkstats(vd)
    nl()

    print("Add key/values, like vdict['a'] = 1.")
    for k, v in zip(['a','b','c'], [1, 2, 3]):
        print('Add ', k, v)
        vd[k] = v


    checkstats(vd)

    vd.reset()
    print('after reset, changed ', bin(vd.changed))
    nl()

    vd['c'] = 4
    vd['d'] = 7

    print("Set two key/values, one with new key.")
    checkstats(vd)
    nl()

    print('key, index of name in vkeys, binary mask for changed int, ')
    nl()
    for k in vd.keys:
        print( 'Index of ', k, ' is ', vd.vkeys.index(k), ' with changed mask', bin(pow(2, vd.vkeys.index(k))))
    nl()
    
    
    print('Reset changed')
    nl()
    vd.reset()
    
    vu = { 'e': 23, 'f': 44, 'g': 22 }

    nl()
    print('Update from another dict')
    print('vu ', vu)
    vd.update(vu)
    nl()
    
    checkstats(vd)

    e = vd['e']
    vd.reset('e')
    print('"e" reset -> vkeys changed ', vd.keys_changed())
    nl()
    
    print('vdict.items()')
    for k, v in vd.items():
        print( k, v, sep=' = ')
    nl()
    
    print('Fetch and reset single or list of keys')
    print('vkeys changed ', vd.keys_changed())
    items = vd.fetch(['f', 'g'])
    print("fetched ['f', 'g'], returning items", items)
    print('vkeys changed ', vd.keys_changed())
    nl()
    
    print('DELETED', DELETED)
    nl()
    vd['a'] = 4444
    vd['d'] = [ 1, 2, 3]
    vd['c'] = DELETED
    
    print('vd ( raw dict, not vdict.keys) ')
    print(vd)
    nl()
    print("vd['c'] == DELETED ", vd['c'] == DELETED)
    nl()
    
    print('len(vdict) ', len(vd))
    print("vdict.get('a')         ", vd.get('a'))
    print("vdict.get('xxx', None) ", vd.get('xxx', None))
    print('vdict.keys  ', vd.keys)
    print('vdict.items ', vd.values)
    nl()
    
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
        x = vd['a']
    except:
        print("It's gone ...")

    nl()


    # print(locals())
    

    

        

