"""
module:     iomapper
version:    v0.0.1
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

IOMapper is a generalization of external bind requests, hiding details
that the main 'controller' application doesn't need to know, the 
gritty 'how to' mechanism of determining call structure and marshalling
parameters.

Use cases:
- IOMapper subclassed with all object references in the namespace, ex.
  See example below for 'Imaginary Devices'.
- IOMapper gets all object references from the values dict.
  See example for 'getters/setters'.  
"""


from functools import partial
from collections import namedtuple
from lib.vdict import VolatileDict, checkstats
from lib.getset import itemgetter, itemsetter, attrgetter, attrsetter

i_get, i_set = itemgetter, itemsetter   # by index, list or dict
a_get, a_set = attrgetter, attrsetter   # by attribute, object

DEBUG = False


"""Poor man's typing"""
def x():
    return None
   
deftype = type(x)

class XX():
    def meth(self, x ):
        return None
        
xx = XX() 

methtype = type(xx.meth)

del(x, xx, XX)

""" ### Map ###

wrap    - itemgetter or itemsetter
target  - function name or parameter for itemsetter 
params  - list of key names for the values dict
vreturn - key name of value to update in the values dict
chain   - key for function(s) in the iom dict, post-processing
           mostly for synch of values in values dict.  

3 situations

wrap          target          params
----------    ----------      ----------
getter        None           obj to be gotten from  #   wrap(params), that is reader(source)
setter        obj to update  new value              #   wrap(target, value)
None          func(partial)  params to eval (list)  #   target(params)

In all cases, if the vreturn==None or value in dict is same, the return is ignored.

"""
mnames = ['wrap',     # get or set 'wrap action', or func call as a 'get' type
          'target',   # target of write ( update), wrap is setter
          'params',   # param of wrap if target = None, else params names for target
          'vreturn',  # key in values dict to set to return value
          'chain']    # function key in the iom dict, mostly for synch of values.   

Map = namedtuple( 'Map', mnames )

mgetter = attrgetter( *mnames )

def mget( iom:dict, key:str ) -> tuple:
    """Map getter, for unpacking """
    return mgetter(iom[key])


class IOMapperError(Exception):
    pass

class IOMapper(object):
    """Fulfill data or function bind requests to IO actions using Map defs.
    
       - iomap:dict - bind request keywords and Map defintions.
       
       - values:VolatileDict - *external* dict with key/values for parameters
         and returns.  Most of the actual activity is in set/get of k/vs
         and then iom.read/bind using values dict values for parameters.
         
       - transforms:dict - massage return values ( ex. voltage -> degrees )
    
       When subclassed, becomes static info structure.  Will need to create
       IOM with kws: IOMapperSub(values=x) or just (None,x, None)
       
       @properties must be wrapped in attrgetter(propname).
       
       
    """

    _iomap = {}   # subclassed if not empty, are static structures
    _transforms = {}

    def __init__(self,
                 iomap:dict=None,
                 values:VolatileDict=None,
                 transforms:dict=None,
                 *args, **kwargs):

        if self._iomap:   # subclassed, overide iomap
            self.iomap = self._iomap
            self.transforms = self._transforms
        elif iomap:
            self.iomap = iomap
            self.transforms = transforms or {}
        else:
            raise IOMapperError('Need to provide non-empty dict of mappings.')

        if values:  # None or empty
            self.values = values
        else:
            raise IOMapperError('Need to provide non-empty dict of values')
            
        # self.read_into_values()   # auto init values dict or manual sync  ?


    def read(self, key:str ) -> 'Any':
        """Bind a data/functional key/value. Read into the values dict."""
    
        wrap, target, params, vreturn, chain = mget(self.iomap, key)
        
        if DEBUG:
            print("DEBUG: In reading key ", key )
        
        if isinstance(chain, str):
            chain = [chain]

        v = self.bind(wrap, target, params)
        
        if vreturn and v!=self.values[vreturn]:
            if key in self.transforms and v is not None:
                self.values[vreturn] = self.transforms[key](v) 
            else:
                self.values[vreturn] = v  # whatever, may be None
            return self.values[vreturn]
            
        if chain:   # post-processing, note is recursive
            for ch in chain:
                if DEBUG:
                    print("Chaining for iom key ", ch, '  -> None' )
                self.read(ch)  # no returns, mostly for values dict sync

        return v  # why not, likely None
        
    def write(self, key:str ) -> 'Any':
        """Reads/in and writes/out are the same thing from a mapping
           perspective.  Strange construct but maybe more readable code. """ 
    
        return self.read(key)  
          

    def read_into_values(self):
        """Bind all read functional keys in IO Map to values dict.
           Reading only, no state change so no chain."""

        reads = [ k for k in self.iomap.keys() 
                     if self.iomap[k].vreturn] # not None or []
        for key in reads:
            wrap, target, params, vreturn, chain = mget(self.iomap, key)
            v = self.bind(wrap, target, params)
            if vreturn and v!=self.values[vreturn]:
                if key in self.transforms and v is not None:
                    self.values[vreturn] = self.transforms[key](v) 
                else:
                    self.values[vreturn] = v  # whatever, may be None


    def bind(self, wrap, target, params ) -> 'Any':
        """Bind either data in values dict or bind atribute in object.
           Similar to a simple function call, either wrapped or not."""
        # if not hasattr(wrap, '__name__'):  # closure, not function, for mpy ?

        if DEBUG:
            print()
            print(f'DEBUG:  w: {wrap} / t: {target} / p: {params}' )
        
        if isinstance(target, str):
            target = self.values[target]
            
        if isinstance(params, str):
            params = [params]
        
        if DEBUG: print('params ', params )
        
        if params:
            evals = [ self.values[p] if isinstance(p, str) else p for p in params ]
        else:
            evals = []
        
        if DEBUG: print('evals ', evals)

        if target is None:   # is getter
            
            if DEBUG:
                print('target is None')
                print()
            return wrap(*evals)
                
        else:   # is function call or setter
        
            if DEBUG: print('target is not None')
            if wrap is None:  
                if evals:   # need ? 
                    if DEBUG:
                        print('params eval ', evals )
                    return target(*evals)
                else:
                    if isinstance(target, (deftype, methtype)):  # others ?
                        return target()
                    else:  
                        return target  # property ?, should be wrapped with attrgetter
            else:
                if DEBUG:
                    print(f'setter for {wrap} with {evals}')
                    print()
                return wrap(target, *evals)

        raise IOMapperError(f"Can't bind {wrap} | {target} | {params} | {evals} -> .")



if __name__ == '__main__':



    nl = print
    
    """Imaginary Devices""" 
    
    class Fan(object):
        
        OFF:int = 0
        ON:int  = 1
        
        def __init__(self, *args, **kwargs):

            self.state = self.OFF
            
        def set_state(self, new_state:int, verbose:bool=False ):
        
            if verbose:
                if new_state == self.OFF:
                    print('-> Turning fan OFF')
                elif new_state == self.ON:
                    print('-> Turning fan ON')
                else:
                    print('-> Unknown fan state: ', new_state) 
        
            self.state = new_state
         
        def get_state(self):
        
            return self.state
            
    fan = Fan()
    
    class LED(object):
    
        RED:tuple   = ( 255, 0, 0 )
        GREEN:tuple = ( 0, 255, 0 )
        BLUE:tuple  = ( 0, 0, 255 )
        WHITE:tuple = ( 255, 255, 255 )
        OFF:float   = 0.0    #  0.0 -> 1.0
        ON:float    = 1.0
    
        def __init__(self, *args, **kwargs):

            self.color:tuple = self.RED        
            self.brightness:float = self.ON  
                          
        def set(self, color:tuple=None, brightness:float=None):
            """led.set() works like reset to default"""
        
            if color:
                self.color = color  
            if brightness is not None:  # could be 0.0
                self.brightness  = brightness
       
        @property
        def get_state(self):
        
            return ( self.color, self.brightness )
            
    led = LED() 
    

    def temperature():
        return 20.2
        
    def calibrate_temp(t:float) -> float:
        return t * 1.3
    
    nl()
    print('### basic function binding ###')
    nl()


    io = {'get_temp':     Map( wrap=None,   
                            target=temperature,
                            params=None,
                            vreturn='room_temp',
                            chain=None ),
                            
          'fan_on':       Map( wrap=None,   
                            target=partial(fan.set_state,verbose=True),
                            params=['fan_ON'],
                            vreturn=None ,
                            chain=['fan_status', 'led_GREEN']),
          'fan_off':      Map( wrap=None,   
                            target=fan.set_state,
                            params=['fan_OFF'],
                            vreturn=None,
                            chain=['fan_status', 'led_RED']),
          'fan_status':   Map( wrap=None,   
                            target=fan.get_state,
                            params=[],
                            vreturn='fan_state',
                            chain=None),
                            
          'led_on':       Map( wrap=None,   
                            target=led.set,
                            params=[None, led.ON],  # need positional or partialed
                            vreturn=None,
                            chain='led_status'),
          'led_off':      Map( wrap=None,   
                            target=led.set,
                            params=[None,led.OFF],
                            vreturn=None,
                            chain='led_status'),
          'led_RED':       Map( wrap=None,   
                            target=led.set,
                            params=[led.RED],
                            vreturn=None,
                            chain='led_status'),
          'led_GREEN':      Map( wrap=None,   
                            target=led.set,
                            params=[led.GREEN],
                            vreturn=None,
                            chain='led_status'),
          'led_status':   Map( wrap=a_get('get_state'),  # @properties must be wrapped 
                            target=None, 
                            params=[led],
                            vreturn='led_state',
                            chain=None), 
                       
                       }

    vd = VolatileDict([('room_temp',10.1),
                      ('fan_ON', Fan.ON),
                      ('fan_OFF', Fan.OFF),
                      ('fan_state', Fan.OFF),
                      ('led_state', (LED.RED, LED.ON))])  # only list of k/v tuple pairs
                      
    vd.read_only.extend(['fan_ON', 'fan_OFF'])  # constants  

    trform = { 'other': int,
              'get_temp': calibrate_temp }

    iom = IOMapper(io, vd, trform)

    print('dir(iom)')
    print(dir(iom))
    nl()
    
    print('iomap')
    for k, v in iom.iomap.items():
        print(k, ': ', v)
    nl()
        
    print('values before: ', vd )

    print("iom.read('get_temp') ->", iom.read('get_temp'))
    
    print('values after: ', vd )
    nl()
    print('Directly set values in values dict')
    nl()
    
    vd['room_temp'] =  227.3
    vd['fan_state'] = 44
    vd['led_state'] = 44
    print('values after incorrect update of ', vd )
    nl()
    
    print('Init values dict - read_into_values()')
    iom.read_into_values()
    
    nl()
    checkstats(vd)
    
    print('value_dict fetch room_temp ->' , vd.fetch('room_temp'))
    nl()
    
    checkstats(vd)
    
    print('reset changed')
    vd.reset()
    nl()

    print("iom.write('fan_on') -> partialed to verbose=True")    
    iom.write('fan_on')
    nl()    
    checkstats(vd)
    print("Note that function key chain updates value_dict 'fan_state' \n\
and 'led_state' so values are in sync with fan.ON.")
    print()
    

    print('reset changed')    
    vd.reset()
    nl()
    
    print("iom.write('fan_off'), should be verbose=False ")    
    iom.write('fan_off')
    print("iom.write('led_off')")    
    iom.write('led_off')
    nl() 
    
    # iom.read_into_values()
    
    checkstats(vd)
    nl()
    
    del(iom)
    

    print('### getters/setters ###') 
    
     
    
    class SomeObject:
    
        def __init__(self, a, b, c ):
        
            self.a = a
            self.b = b
            self.c = c
            
    some_obj = SomeObject(111, 222, 333 )
    
    some_dict = { 'seven': 7 , 'eight': 8, 'nine': 9 } 
    
    some_list = [ 77, 88, 99 ]
    
    some_tuple = ( 'Bill', '22 Anywhere Lane', '234-555-6789' )

    # using values dict only, no direct obj references.

    iom2 = { 'so_get_a':     Map( wrap=a_get('a'),
                                 target=None,
                                 params='some_obj',
                                 vreturn='a',
                                 chain=None), 
              'so_set_a':      Map( wrap=a_set('a'),
                                 target='some_obj',
                                 params='newval',
                                 vreturn=None,
                                 chain='so_get_a'), 
                           
              'sd_get_seven' : Map( wrap=i_get('seven'),
                                 target=None,
                                 params='some_dict',
                                 vreturn='seven',
                                 chain=None),                                  
              'sd_set_seven':  Map( wrap=i_set('seven'),
                                 target='some_dict',
                                 params='newval',
                                 vreturn=None,
                                 chain='sd_get_seven'), 
                                 
              'sl_get_first':  Map( wrap=i_get(0),
                                 target=None,
                                 params=['some_list'],
                                 vreturn='first',
                                 chain=None),                                  
              'sl_set_first': Map( wrap=i_set(0),
                                 target='some_list',
                                 params='newval',
                                 vreturn=None,
                                 chain='sl_get_first'), 
                                 
              'st_get_phone': Map( wrap=i_get(2),
                                target=None,
                                params=['some_tuple'],
                                vreturn='phone',
                                chain=None), 
              # no setter
            }
                                
    vd2 = VolatileDict([('a', 0), ('some_obj', some_obj),
                        ('seven', 0), ('some_dict', some_dict),
                        ('first', 0), ('some_list', some_list),
                        ('phone', ''), ('some_tuple', some_tuple),
                        ('newval', 9999)])
                        
    # constant references
    vd2.read_only.extend(['some_obj', 'some_dict', 'some_list', 'some_tuple']) 
                        
    
    nl()                    
    print('iom2')
    
    for k, v in iom2.items():
        print(k, ': ', v)
    nl()
    print('vd2')
    print(vd2)
    print('reset vd2')
    vd2.reset()
    nl()   
                        
     
    iomap2 = IOMapper(iom2, vd2)                

    print("iomap2.read('so_get_a')")
    print("-> ", iomap2.read('so_get_a'))
    print("iomap2.write('so_set_a')")
    print('-> ', iomap2.write('so_set_a'))
    print("vd2['some_obj'].a ")
    print(vd2['some_obj'].a)
    nl()
    
    print("iomap2.read('sd_get_seven')")
    print("-> ", iomap2.read('sd_get_seven'))
    print("iomap2.write('sd_set_seven')")
    print("-> ",  iomap2.write('sd_set_seven'))
    nl()
    
    print("iomap2.read('sl_get_first')")
    print("-> ", iomap2.read('sl_get_first'))
    print("iomap2.write('sl_set_first')")
    print("-> ",  iomap2.write('sl_set_first'))
    nl()
    
    print("iomap2.read('st_get_phone')")
    print("-> ", iomap2.read('st_get_phone'))
    nl()
    

    
    nl()
    checkstats(vd2)
    
    print("Note that phone did not change but the 'phone' value in values dict did.")
    nl()
    
    # print(iomap2.iomap['so_set_a'].params)
    print('END')


    print()


    

    
    
