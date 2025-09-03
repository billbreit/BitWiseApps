"""
module:     iomapper
version:    v0.0.2
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

IOMapper is a generalization of external bind requests, hiding details
that the main 'controller' application doesn't need to know, the
gritty 'how to' mechanism of determining call structure and marshalling
parameters.

Use cases:
- IOMapper subclassed with all object references in the namespace,
  See example below for 'Imaginary Devices'.
- IOMapper gets all object references from the values dict.
  See example for 'getters/setters'.
  
An 'agenda' feature maintains consistency across cycles by generating
write commands for a new 'read_into_values' cycle.  In other words
values changed are in fact changed, as required by IOEngine run_cycle,

IOMapper object state is determined by the keys and values in values dict,
*plus* the commands in the agenda from the previous binding cycle.
   
"""

from collections import namedtuple

from lib.core.functools import partial
from lib.core.getset import i_get, i_set,  a_get, a_set
from lib.vdict import VolatileDict, RO, checkstats

MDEBUG = False  # need for both code debugging and iomap debugging
EDEBUG = False  # name clash with EDEBUG in IOEngine

"""Poor man's typing"""
def x():
    return None
deftype = type(x)

class XX():
    def meth(self, x ):
        return None
xx = XX()
methtype = type(xx.meth)

def XXX(func):

    def wrap_func(*args, **kwargs ):
        r = func(*args, **kwargs)
        return r

    return wrap_func
xxx = XXX(property)
wraptype = type(xxx)  # <closure> in mpy

del(x, xx, XX, xxx, XXX)

""" ### Map ###

Basic namedtuple structure for mapping requests to calls.

wrap    - item/attr getter or item/attr setter
target  - function name or parameter for item/attr setter
params  - list of key names for the values dict
vreturn - key name of value to update in the values dict
chain   - key for function(s) in the iom dict, post-processing
           mostly for synch of values in values dict.

3 basic situations

wrap          target          params
----------    ----------      ----------
getter        None           obj to be gotten from  #   wrap(params), that is reader(source)
setter        obj to update  new value              #   wrap(target, params), params are values)
None          func(partial)  params to eval (list)  #   target(*params) or target(**params)

In all cases, if the vreturn==None or value in dict is same, the return is ignored.

@properties need to be wrapped with attrgetter(propname).

Keywords are supported by a single dict in Map.params:
   Map.params={'myvar':123}  or
   Map.params='my_param' for 'my_param':{'myvar':123} in values dict

To pass the dict itself as a parameter:
   Map.params=[{'myvar':123}] or
   Map.params='my_param' for 'my_param':[{'myvar':123}]

Haven't figured out mixed positional and keyword calls, can pass a dict
param to a stub function and let it resolve **dict keywords. TBD
"""

mnames = ['wrap',     # wrapper: get or set 'wrap action', or func-> func as 'constructor'
          'target',   # func: target of write ( update), wrap is setter
          'params',   # list['Any']: param of wrap if target = None, else values key names for target
          'vreturn',  # str: key in values dict to set to return value
          'chain']    # list[str]: action keys in the iom dict, *unconditionally* executed,
                      # mostly for synch of values, deps. of vreturn above or
                      # external state of something ( a server, a device, etc. )

Map = namedtuple( 'Map', mnames )

mgetter = a_get( *mnames )

def mget( iom:dict, key:str ) -> tuple:
    """Map getter, for unpacking """
    return mgetter(iom[key])

def MM( wrap:'funcref'=None,
        target:'funcref'=None,
        params=None,
        vreturn=None,
        chain=None) -> Map:
        """Simple MakeMap helper function ( no namedtuple defaults in mpy ).
       Probably more 'namedtuple plus' checks and validations here.

       { 'actionkey': Map( wrap = None,
                           target = myobj.settval,
                           params = ['thenewval'],
                           vreturn = None,
                           chain = None ) }

       { 'actionkey': MM( target = myobj.settval,
                          params = ['thenewval'] }

       """
        mwrap = wrap
        mtarget = target
        mparams = params or []
        mvreturn = vreturn
        mchain = chain or []

        return Map(wrap = mwrap,
                   target = mtarget,
                   params = mparams,
                   vreturn = mvreturn,
                   chain = mchain)

""" IOMapperDef

    values:VolatileDict - source of all values, very dynamic.
                          Can be defined and owned externally to iomapper.

    iomap:dict - key/value action name/Map structures as above

    read_keys:list[str] - action keys required to synch the values dict
                          with external state, triggering chain actions
    local_values:dict - export names:references of local objects to IOEngine

    transforms:dict - transform values returned into values in the values dict.

    This structure is used with values dict as IOMapper(values_dict,*iomapper_def ).

    Values dict must be either be passed to IOMapper (externally owned), or
    defined in a specialized subclass with the option of overriding.
"""

iomapper_fields = ['values', 'iomap', 'read_keys', 'local_values', 'transforms']

IOMapperDef = namedtuple('IOMapperDef', iomapper_fields )

# Commands for the agenda mechanism, pass actions forward to next binding cycle,
# maintain valid values_changed flags.

SetVal = namedtuple('SetVal', ['key', 'value'])  # value needs indirection
Run = namedtuple('Run', ['action'])    # params override ?


class IOMapperError(Exception):
    pass

class IOMapper(object):
    """Fulfill data or function bind requests to IO actions using Map defs.

       - values:VolatileDict - dict with key/values for parameters and
         returns.  Most of the actual activity is in set/get of k/vs
         and then iom.read/bind using values dict values for parameters.

       - iomap:dict - bind request keywords and Map defintions.

       - read_keys:list[str] - action keys for read cycle.  Most will have a
         vreturn to the values dict and then a chain of action keys that
         synchronize the dependent values.

       - local_values: dict[str, obj_ref - local 'external' object refs
         to add to value dict.  Many be used externally to augment 
         or bypass iomapper functions, if necessary. Can be passed as params,
         but better defined in subclass.

       - transforms: dict - massage return values ( ex. voltage -> degrees )
       
       The internal structure agenda is a list of SetVal/Run commands to be
       run before a new binding cycle and is part of IOMapper state.

       When subclassed, becomes static info structure, more like a
       specialization than a subclass.
    """

    # for 'subclassing' or specialization, keeps namespace uncluttered

    _values:VolatileDict = None  # dynamic, can be None in subclass def
                                 # and then passed to __init__
    _iomap:dict = None           # the rest are static
    _read_keys:list=None
    _local_values:dict = None
    _transforms:dict = None

    def __init__(self,
                 values:VolatileDict=None,
                 iomap:dict=None,
                 read_keys:list=None,
                 local_vals:dict = None,
                 transforms:dict=None):

        if MDEBUG:
            print('### In IOMapper __init__')
            print()

        if values:   # may be specialized, override _values default
            self.values = values
        else:
            # use subclass def,
            self.values = self._values

        # if not hasattr(self, 'values') or not self.values:  # None or empty
        if not self.values:  # None or empty
            raise IOMapperError('Need to provide non-empty dict of values')

        if self._iomap:   # subclass, override params
            self.iomap = self._iomap
            self.read_keys = self._read_keys
            self.transforms = self._transforms
        elif iomap:
            self.iomap = iomap
            self.read_keys = read_keys or []
            self.transforms = transforms or {}
        else:
            raise IOMapperError('Need to provide non-empty dict of mappings.')

        if MDEBUG:
            print('IOMap:')
            for k, v in self.iomap.items(): print(f"{k:12}: {v}")
            print()

        # extract any action keys with a vreturn, maintaining key order,
        # can trigger chains so read_keys are the default read order.
        self.all_vreturns = [ k for k in self.iomap.keys()
                                if self.iomap[k].vreturn]  # not None and not ''
        if MDEBUG:
            print('IOMapper: all vreturns ', self.all_vreturns )

        # Now the Values Dict

        if MDEBUG:
            print('IOMapper: initial values: ')
            print(self.values)
            print()
        self.local_vals = self._local_values if self._local_values else local_vals

        # if local_vals, update values dict
        if self.local_vals:
            if MDEBUG:
                print('IOMapper: _local values: ')
                print( self.local_vals)
                print()

            # Fix, need to revisit, no slam for existing values dict
            # if set(self.local_vals).intersection(set(self.values)):
            #    raise IOMapperError('Duplicate keys in values and local_values dicts.')
            # else:
            # self.values.update(self.local_vals)
            #self.values.read_only.extend(self.local_vals.keys())
            
            for k, v in self.local_vals.items():
                if k not in self.values:
                    self.values[k] =v
                    self.values.read_only.append(k)
                    
        self.agenda = []

        if MDEBUG:
            print('Starting read_into_values')
        self.read_into_values(self.all_vreturns)  # auto initialize, default 'all'
        if MDEBUG:
            print('IOMapper: initialized values: ', self.values)
            print()


    def read(self, key:str ) -> 'Any':
        """Bind a data/functional key/value. Read into the values dict."""

        wrap, target, params, vreturn, chain = mget(self.iomap, key)

        if MDEBUG:
            print()
            print('Read/write action key:', key, ' vreturn:', vreturn ,
                 ' chain:', chain )

        v = self.bind(wrap, target, params)

        if key in self.transforms and v is not None:
            v = self.transforms[key](v)

        if vreturn and v!=self.values[vreturn]: # rethink, ignore v if None ?
            self.values[vreturn] = v  # whatever, not same value

        if isinstance(chain, str):
            chain = [chain]

        if chain:   # post-processing, note can be recursive, careful.
                    # May pass values forward via values dict
                    # Updates to same vdict key within chain are bug bait.
            for ch in chain:
                r = self.read(ch)  # no returns, mostly for values dict sync
                if MDEBUG:
                    print(f"Chaining for {ch} - returning -> {r}")

        return v  # why not, likely None

    def write(self, key:str ) -> 'Any':
        """Reads/in and writes/out are the same thing from a mapping
           perspective.  Strange construct but maybe more readable code
           to indicate an intended state change. """

        return self.read(key)
        
    def add_agenda(self, agenda):
        """Add command ( SetVal or Run ) for next cycle."""

        if isinstance(agenda, list):
            self.agenda.extend(agenda)
        else:
            self.agenda.append(agenda)
        
    def run_agenda(self):
        """Execute commands from previous cycle at start of new cycle,
           generating values_change."""
           
        if MDEBUG or EDEBUG: print('-> Running agenda')

        for command in self.agenda:
            if isinstance(command, SetVal):
                if MDEBUG or EDEBUG: print('     SetVal ', command.key, command.value)
                self.values[command.key] = command.value
            elif isinstance(command, Run):
                if MDEBUG or EDEBUG: print('     Run ', command.action)
                self.write(command.action)
            else:
                raise IOMapperError(f'Unsuppurted agenda item {command}.')

        if MDEBUG or EDEBUG: print()
        
        self.agenda = []


    def read_into_values(self, read_keys:list=None ):
        """Bind all read keys in IO Map to values dict.
           In principle, should be reading only, with no state change
           and therefore no chain.  May not be true, ex. pop->return.

           Needs review, maybe list of scheduled reads ...

           vreturn not None, params None    , wrap is getter, chain is None
           vreturn not None, wrap not None  , target is None, is getter
           vreturn not None, target not None, params is None, then is read ? """
           
        self.values.reset()
        
        if self.agenda:
            self.run_agenda()

        if read_keys:
            reads = read_keys  # override
        elif self.read_keys:
            reads = self.read_keys  # as defined
        else:
            reads = self.all_vreturns # default, anything with vreturn

        for key in reads:

            wrap, target, params, vreturn, chain = mget(self.iomap, key)
            if MDEBUG:
                print()
                print('Read/write action key:', key, ' vreturn:', vreturn ,
                     ' chain:', chain )
            v = self.bind(wrap, target, params)  # try exception and handle here ?
            if vreturn and v!=self.values[vreturn]:
                if key in self.transforms and v is not None:  # need to filter None ?
                    self.values[vreturn] = self.transforms[key](v)
                else:
                    self.values[vreturn] = v  # whatever, may be None

    def bind(self, wrap, target, params ) -> 'Any':
        """Bind either data in values dict or bind atribute in object.
           Similar to a simple function call, either wrapped or not."""
        # if not hasattr(wrap, '__name__'):  # closure, not function, for mpy ?

        if MDEBUG:
            print('start bind()')
            print(f'wrap: {wrap} | target: {target} | params: {params}' )

        if isinstance(target, str):
            target = self.values[target]

        if isinstance(params, str):
            params = [params]

        if MDEBUG: print('params ', params )

        # resolve values for params
        if params:
            if isinstance(params, dict):
                # is dict of keywords/values, func(**dict)
                evals = params
            else:
                # is list of value keys and objects to be passed, func(*list)
                evals = [ self.values[p] if isinstance(p, str) and p in self.values
                                         else p for p in params ]
        else:
            evals = []

        if target is None:   # is getter
            if MDEBUG:
                print('target is None')

            result = wrap(*evals)
            if MDEBUG:  print(f'bind() returning -> {result}')
            return result

        else:   # target is function or setter

            if wrap is None:  # is function
                if evals:
                    if MDEBUG:
                        print('params eval ', evals )

                    if isinstance(evals, dict): # by keyword in dict, retest ?
                        if MDEBUG: print('In target(dict) - evals ', evals)
                        result = target(**evals)
                    else:
                        result = target(*evals)
                else:
                    if isinstance(target, (deftype, methtype)):  # others ?
                        result = target()
                    else:
                        result = target  # property ?, should be wrapped with attrgetter

            else:  # is setter
                if MDEBUG: print(f'setter for {wrap}, with {target} {evals}')
                result = wrap(target, *evals)

            if MDEBUG: print(f'exit bind() - returning -> {result}')
            return result

        raise IOMapperError(f"Can't bind {wrap} | {target} | {params} | {evals} -> .")


if __name__ == '__main__':

    from random import random

    nl = print

    MDEBUG = True

    """Imaginary Devices"""

    from idevices import Fan, LED

    fan = Fan()
    led = LED()

    ### Stub/Helper Functions

    def temperature():
        return round(20 + ( 4 - 5*random()),2)

    def calibrate_temp(t:float) -> float:
        return t * 1.3

    nl()
    print('### IOMapper Test')
    print('### Basic Function Binding')
    nl()

    # MM is MakeMap function -> Map with defaults, None or []

    # RO is read only
    vd = VolatileDict([('room_temp',10.1),
                      RO('fan_ON', Fan.ON),
                      RO('fan_OFF', Fan.OFF),
                      ('fan_state', Fan.OFF),
                      ('led_state', (LED.RED, LED.ON)),
                      RO('led_off_param', {'brightness': led.OFF}),  # keywords, dict not list
                      ]) # only list of k/v tuple pairs

    iom = {'get_temp':    MM( target=temperature,
                               vreturn='room_temp'),

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
                            params=[None, led.ON],  # need positional None
                            vreturn=None,
                            chain='led_status'),
          'led_off':      Map( wrap=None,
                            target=led.set,
                            # params='led_off_param',
                            params={'brightness': led.OFF}, # keywords, dict not list
                            vreturn=None,
                            chain='led_status'),
          'led_RED':      MM( target=led.set,
                            params=[led.RED],
                            chain='led_status'),
          'led_GREEN':    MM( target=led.set,
                            params=[led.GREEN],
                            chain='led_status'),
          'led_status':   MM( wrap=a_get('get_state'),  # @properties must be wrapped
                            params=[led],
                            vreturn='led_state')
                       }


    trform = { 'get_temp': calibrate_temp }


    iom = IOMapper(vd, iom, transforms=trform)

    del(vd)
    nl()

    print('values before get_temp: ', iom.values )

    print("iom.read('get_temp') ->", iom.read('get_temp'))
    nl()
    print('values after: ', iom.values )
    nl()
    print('Directly set values in values dict')
    nl()

    iom.values['room_temp'] =  227.3
    iom.values['fan_state'] = 44
    iom.values['led_state'] = 44
    print('values after incorrect update of ', iom.values )
    nl()

    print('=== Init values dict - read_into_values() ===')
    iom.add_agenda(SetVal('testsetval', True ))
    iom.add_agenda(Run('fan_on'))
    iom.read_into_values()

    nl()
    checkstats(iom.values)

    print('Reset and read_into_values() with intialized values dict')
    iom.values.reset()
    iom.read_into_values()

    nl()
    checkstats(iom.values)

    print('value_dict fetch room_temp ->' , iom.values.fetch('room_temp'))
    nl()

    checkstats(iom.values)

    print('reset changed')
    iom.values.reset()
    nl()

    print("iom.write('fan_on') -> partialed to verbose=True")
    iom.write('fan_on')
    nl()
    checkstats(iom.values)
    print("Note that function key chain updates value_dict 'fan_state' \n\
and 'led_state' so values are in sync with fan.ON.")
    print()

    print('reset changed')
    iom.values.reset()
    nl()

    print("iom.add_agenda(Run('fan_off'))")
    iom.add_agenda(Run('fan_off'))
    print("iom.add_agenda(Run('led_off'))")
    iom.add_agenda(Run('led_off'))
    nl()
    iom.read_into_values()

    checkstats(iom.values)
    nl()

    # del(iom)

    print('### Test IOMapper getter/setter wrappers ###')
    nl()

    class SomeObject:

        def __init__(self, a, b, c ):

            self.a = a
            self.b = b
            self.c = c

    some_obj = SomeObject(111, 222, 333 )

    some_dict = { 'seven': 7 , 'eight': 8, 'nine': 9 }

    some_list = [ 77, 88, 99 ]

    some_tuple = ( 'Bill', '22 Anywhere Lane', '234-555-6789' )

    Person = namedtuple('Person', ['name', 'address', 'phone'])

    some_ntuple = Person(*some_tuple )

    # using values dict only, no direct obj references,
    # except for get/sets, JSONible as str->namedtuple ?
    # RO() is read only, MM() is make map.

    vd2 = VolatileDict([('a', 0),
                        RO('some_obj', some_obj),
                        ('seven', 0),
                        RO('some_dict', some_dict),
                        ('first', 0),
                        RO('some_list', some_list),
                        ('phone', ''),
                        RO('some_tuple', some_tuple),
                        ('address', ''),
                        RO('some_ntuple', some_ntuple),
                        ('newval', 9999)])

    iom2 = { 'so_get_a':       MM( wrap=a_get('a'),
                                  params='some_obj',
                                  vreturn='a'),
              'so_set_a':      MM( wrap=a_set('a'),
                                  target='some_obj',
                                  params='newval',
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
              'snt_get_address': Map( wrap=a_get('address'),
                                target=None,
                                params=['some_ntuple'],
                                vreturn='address',
                                chain=None),
              # no setter
            }



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

    iomap2 = IOMapper(vd2, iom2)

    del(vd2, iom2)

    print("iomap2.read('so_get_a')")
    print("got -> ", iomap2.read('so_get_a'))
    nl()
    print("iomap2.write('so_set_a')")
    print('got -> ', iomap2.write('so_set_a'))
    nl()
    print("iomap2.values['some_obj'].a ")
    print(iomap2.values['some_obj'].a)
    nl()

    print("iomap2.read('sd_get_seven')")
    print("got -> ", iomap2.read('sd_get_seven'))
    nl()
    print("iomap2.write('sd_set_seven')")
    print("got -> ",  iomap2.write('sd_set_seven'))
    nl()

    print("iomap2.read('sl_get_first')")
    print("got -> ", iomap2.read('sl_get_first'))
    nl()
    print("iomap2.write('sl_set_first')")
    print("got -> ",  iomap2.write('sl_set_first'))
    nl()

    print("iomap2.read('st_get_phone')")
    print("got -> ", iomap2.read('st_get_phone'))
    nl()

    print("iomap2.read('snt_get_address')")
    print("got -> ", iomap2.read('snt_get_address'))
    nl()

    checkstats(iomap2.values)

    print("Note that phone did not change but the 'phone' value in values dict did.")
    nl()

    print('END')

    print()

    # print('locals ', locals())







