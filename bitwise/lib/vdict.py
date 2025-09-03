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

    - All state changing methods ( vdict.__del__ and vdict.pop ) are protected 
      by a lock mechanism.  May 'row locking' later, which would guarantee
      validity of shared references with access masks on the row/dict key level
      
    -  vdict.popitem not supported.  Key deletes suppported, but not recommended for
       'volatile' scenarios.  Use DELETED tuple.    

    -  Use k-v tuple pairs to maintain order of entry, OrderedDict equivalent.

    - Can be used like OrderedDict where none, some low-memory upython builds.
      Implements dict.update - may not be supported on small builds.

    - Note: micropython base class inheritence is much improved, but it won't run
      on old versions of CircuitPython, try OrderedDict.  However,
      OrderedDict is still not the default on many mpy builds.

    Works with Python v3.9+ and micropython v1.20.0 on a RP Pico
    Does not work with Circuit Python, can't subclass dict without
    recursive crash.

    Some of the design limitations are artificial.  New writer->reader relations can be
    added and deleted at will, but it's not clear why do it under most 'tightly coupled'
    usage scenarios.  Some sort of namespacing and 'namedspace merge' might be more useful.

    Both mpy dict and vdict are signifcantly faster than mpy OrderedDict, which
    may not be be availible on limited micropython builds ( under 256K ).

"""

from collections import namedtuple
import _thread    # mpy compat.

# WW python
try:
    from core.bitops import bit_indexes, power2, bit_length, bit_remove
except ImportError:
    from lib.core.bitops import bit_indexes, power2, bit_length, bit_remove

DELETED = namedtuple('DELETED',[])      # as class
# DELETED = namedtuple('DELETED',[])()  # as instance, not class

RO = namedtuple('RO', ['key', 'value']) # dict _init_, flag k/v tuple as read only

class VolatileDictException(Exception):
    pass

""" mpy v1.21.0 dir(dict)
['__class__', '__delitem__', '__getitem__', '__name__', '__setitem__',
'clear', 'copy', 'get', 'items', 'keys', 'pop', 'popitem', 'setdefault',
'update', 'values', '__bases__', '__dict__', 'fromkeys']
"""

class VolatileDict(dict):   # about as fast as MicroPython collections.OrderedDict
    """ Volatile Dictionary, tracks keys of changed items for
         notification/synching.

        - add/modify only, generally all keys will created before using dict

        - Using delete flags rather than del, pop guarantees validity of all shared

          access masks across clients.  Not thread-safe without lock.

        - Can be used like OrderedDict where none, some low-memory upython builds.

        - Can only create vdict from k-v tuple pairs ( not dict ) to maintain order
          of entry, possibly from a database load.  Update does not enforce this
          for possilby unordered dict.

        - Can set dict keys to read only when creating from k/v tuple list,
          flag k/vs as RO ( read only ) via RO namedtuple.  For example,
          VolatileDict([['rw_key', 123 ), RO('ro_key', 123)])

        - _thread.LockType allocated for updates.

        - Note: MicroPython base class inheritence is much improved, but vdict won't
          run on CircuitPython which adheres to older versions of mpy.
    """

    def __init__( self, *args, **kwargs ):

        super().__init__(*args, **kwargs)
        self.vkeys:list = []    # ensure insert order, OrderedDict may not be avail.
        self.changed:int = 0
        self.read_only:list = []  # works like write-once, will add r/o
                                  # key/value if not in vdict, then blocks
                                  # further updates.

        if len(args) > 0:
            if isinstance(args[0], dict):   # preserve insert order, may need param strict=True
                raise  VolatileDictException(f'Init Error: can only create vdict from tuple pairs.')
            self.vkeys = [ kv[0] for kv in args[0] ]
            self.changed |= power2(len(args[0]))-1
            self.read_only = [ kv.key for kv in args[0] if isinstance(kv, RO )]

        self.lock = _thread.allocate_lock()

    def __setitem__(self, key:str, value:'Any' ):
        """ Track changed items """

        if key in self.vkeys and key in self.read_only:
            raise VolatileDictException(f"Read-Only Key: Can not change read-only key '{key}'")

        with self.lock:
            super().__setitem__(key, value)
            if key not in self.vkeys:
                self.vkeys.append(key)  # ensure insert order
            self.changed |= power2(self.vkeys.index(key))

    def __delitem__(self, key:str):
        """ Not really for volatile dict usage, set value to None or DELETED"""

        if key in self.read_only:
            raise VolatileDictException(f"Read-Only Key: Can not delete read-only key '{key}'")

        with self.lock:
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

        return VolatileDict([( key, value ) for key in keys ])

    def copy(self)  -> 'VolatileDict':

        vd = VolatileDict(self.items())
        vd.changed = self.changed
        vd.read_only = self.read_only[:]
        vd.vkeys = self.vkeys[:]
        return vd

    def clear(self):
        """Overrides read only"""

        with self.lock:
            super().clear()
            self.changed = 0
            self.read_only = []
            self.vkeys = []

    def items(self) ->list[tuple]:
        "Ensures insert order, for mpython"
        return [(k, self[k]) for k in self.vkeys]

    def keys(self) -> list:
        return self.vkeys

    @property
    def values(self) -> list:
        """Maintaining order"""
        return [self[k] for k in self.vkeys]

    def setdefault(self, key:str, value=None ) -> 'Any':
        """If key not in dict, add with default. Then return current value."""

        if key not in self.keys():
            self.__setitem__( key, value )

        return self[key]

    def pop(self, key:str) -> 'Any':
        """ Can be used, but not really useful for complex reader/writer
           relationships.  Better set value to DELETED"""

        if key in self.read_only:
            raise VolatileDictException(f"Read-Only Key: Can not pop read-only key '{key}'")
        if key not in self:
            raise  VolatileDictException(f"Key Pop Error: key '{key}' not found.")

        with self.lock:
            item = super().pop(key)
            slot = self.vkeys.index(key)
            self.vkeys.remove(key)
            self.changed = bit_remove(self.changed, slot)

        return item

    def popitem(self):
        """ Not useful for volatile dict, too unpredictable for vdict
            usage scenario,  Set value to None or DELETED"""

        raise NotImplementedError

    def update(self, dictorlist ):
        """Generally run at the  start of the vdict lifecycle.
           Beware: If dictorlist is mpy dict type, key order is
           not guaranteed. Note that mpydict.items doesn't help."""

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

    def reset(self, key:str=None):
        """ If no key, set changed to 0. If key, AND of NOT slot index into changed """

        if key is not None and key not in self.vkeys:
            raise  VolatileDictException(f"Key Reset Error: key '{key}' not found.")

        with self.lock:
            if key:
                self.changed &= ~power2(self.vkeys.index(key))
            else:
                self.changed = 0

    def keys_changed(self) -> list:

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
    print('VDict Stats')
    print('vdict:        ', vdict)
    print('vdict len:    ', len(vdict))
    print('vkeys:        ', vdict.vkeys)
    print('read_only     ', vdict.read_only)
    print('changed mask: ', bin(vdict.changed))
    print('vkeys changed:', vdict.keys_changed())
    print()


if __name__ == '__main__':

    import time
    
