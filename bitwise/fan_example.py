"""Demo of IOMapper

module:     fan_example
version:    v0.0.1
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2025 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

The Fan Mapper is an extended example of IOMapper, driving a process
as defined by IOMap and IOMapper parameters.  The map is from action
keywords to objects methods or APIs of imaginary devices, programs or protocols.
The IOMap and conditions defined in the driver code simulates the a simple
( and inexpensive ! ) fan with some non-simple logic requirements,
plus a few major design problems.

A DEAD FAN Exception happens about one in ten runs.  Maybe reduce the
money-back guarantee from two weeeks to one week ?

"""

try:
    from gc import mem_free, mem_alloc, collect
    mem_free_avail = True
    collect()  # seems to make a difference. why ?
    start_mem = mem_free()
    start_memalloc = mem_alloc()
except:
    mem_free_avail = False


from functools import partial
from random import random

from iomapper import IOMapper, Map

from lib.gentools import chain
from lib.bitops import power2, bit_indexes
# from lib.evaluator import Evaluator, Condition

from lib.vdict import VolatileDict, checkstats
from lib.getset import itemgetter, itemsetter, attrgetter, attrsetter

i_get, i_set = itemgetter, itemsetter   # by index: list, tuple or dict
a_get, a_set = attrgetter, attrsetter   # by attribute: object attr

from idevices import Fan, LED, RandomThermometer, Thermostat, Switch

led = LED()
thermstat = Thermostat()
switch = Switch()

### Stub Classes/Functions for convenience,
### device subclasses, or odd interfaces.

class CheapFan(Fan):
    """The Boss, in his wisdom, has decided use really cheap fan motors,
        which overheat when the internal temp is over 42.0 C ( or
        whataver ) and that destroys the fan.  A fix cheaper
        than a thousand cheap fans ... now, how to deep six those
        pesky Customer Satisfaction Questionnaires ?
    """

    SUSPEND:int = 2
    UNSUSPEND:int = 3  # transient state, restores previous state
    MAXTEMP:float = 40.0
    DEADFAN:float = 42.0

    heat_index = 1.6  # degree gain per cycle, by type of fan

    def __init__(self,*args, **kwargs):

        super().__init__(self, *args, **kwargs )

        self.state_history = [ 0, 0, 0]
        self.internal_temp = 0.0
        self.saved_state = self.OFF

    def overheating(self, temp_hist:list):
        """Estimated internal temp from tests/heuristics"""

        self.internal_temp = sum(temp_hist)/len(temp_hist) + sum(self.state_history) * self.heat_index

        if self.internal_temp > self.DEADFAN:
            raise Exception(f'DEAD FAN ! Internal temp is {self.internal_temp}.')

        return self.internal_temp > self.MAXTEMP

    def set_state(self, new_state:int, verbose:bool=False ):

        if new_state == self.SUSPEND:
            if verbose:
                print('-> Fan overheating, fan SUSPEND')
                print()

            self.saved_state = self.state
            self.state = new_state

        else:
            if new_state == self.UNSUSPEND:
                if verbose:
                    print('-> fan UNSUSPEND, restoring fan state -> ', self.saved_state)
                    print()
                new_state = self.saved_state
            # potentially overriding partial
            super().set_state(new_state, verbose)

    def update_history(self):
    
        if self.state==self.ON:
            self.state_history.append(1)
        else:
            # state = OFF or SUSPEND
            self.state_history.append(0)

        self.state_history.pop(0)

fan = CheapFan()

### Function helpers

def temperature():
    return round(21 + ( 4 - 5*random()),2)

def calibrate_temp(t:float) -> float:
    return round(t * 1.6,2)

def get_upperlimit(temp:float):

    return temp + 0.5

def get_lowerlimit(temp:float):

    return temp - 0.5

def update_temp_hist(temp_history:list, room_temp:float):

    if sum(temp_history)==0:
        return [room_temp]*len(temp_history)

    temp_history.append(room_temp)

    return temp_history[1:]

def update_temp_smoothed( room_temp:float, temp_smoothed:int=0, alpha:int=0.6):
    """May be more realistic thermal effect. Not used yet. """

    if temp_smoothed==0:
        return room_temp

    calc_smoothed = room_temp*alpha + temp_smoothed*(1-alpha)

    return calc_smoothed


class  FanIOM(IOMapper):
    """ Class variables are passed to IOMapper __init__

        Action key / Map to 'external' object (often wrapped) or function

        params: a list of key name of values in the values dict, whcih is
        also 'external' to both the IOMapper and the IOEngine.

        vreturn: updates a key/value in the values dict.

        chain: the next actions to trigger, *unconditionally*, whenever
        'this action' then 'that list of actions'. Condtional actions
        are defined in the IOEngine.

    """
    
    _values = None  # overridden by values parameter

    _iomap = {'get_temp': Map( wrap=None,
                            target=temperature,
                            params=None,
                            vreturn='room_temp',
                            chain=['update_temp_hist']),
           'update_temp_hist': Map( wrap=None,
                            target=update_temp_hist,
                            params=['temp_history', 'room_temp'],
                            vreturn='temp_history',
                            chain=None ),

          'fan_on':       Map( wrap=None,
                            target=partial(fan.set_state,verbose=True),
                            params=['fan_ON'],
                            vreturn=None ,
                            chain=['fan_status', 'led_GREEN']),
          'fan_off':      Map( wrap=None,
                            target=partial(fan.set_state,verbose=True),
                            params=['fan_OFF'],
                            vreturn=None,
                            chain=['fan_status', 'led_RED']),
          'fan_suspend':   Map( wrap=None,
                            target=partial(fan.set_state,verbose=True),
                            params=['fan_SUSPEND'],
                            vreturn=None,
                            chain=['fan_status', 'led_BLUE']),
          'fan_unsuspend':   Map( wrap=None,
                            target=partial(fan.set_state,verbose=True),
                            params=['fan_UNSUSPEND'],
                            vreturn=None,
                            chain=['fan_status']),
          'fan_status':   Map( wrap=None,
                            target=fan.get_state,
                            params=[],
                            vreturn='fan_state',
                            chain=None),
          'fan_overheating':   Map( wrap=None,
                            target=fan.overheating,
                            params=['temp_history'],  # room_temp bound above
                            vreturn='fan_overheated',
                            chain=None),
           'update_fan_hist': Map( wrap=None,
                            target=fan.update_history,
                            params=[],
                            vreturn=None,
                            chain=None ),

          'switch_on':    Map( wrap=None,
                            target=switch.set_state,
                            params=['switch_ON'],
                            vreturn=None ,
                            chain=['switch_status']),
          'switch_off':   Map( wrap=None,
                            target=switch.set_state,
                            params=['switch_OFF'],
                            vreturn=None,
                            chain=['switch_status']),
          'switch_status':  Map( wrap=None,
                            target=switch.get_state,
                            params=[],
                            vreturn='switch_state',
                            chain=None),

           'thermstat_get' :  Map( wrap=None,
                            target=thermstat.get_setting,
                            params=[],
                            vreturn='thermstat_setting',
                            chain=None),
           'thermstat_reset' :  Map( wrap=None,
                            target=thermstat.reset,
                            params=['thermstat_setting'],
                            vreturn=None,
                            chain=['set_upperlimit', 'set_lowerlimit']),
           'set_upperlimit': Map( wrap=None,
                            target=get_upperlimit,
                            params=['thermstat_setting'],
                            vreturn='upper_limit',
                            chain=None),
           'set_lowerlimit': Map( wrap=None,
                            target=get_lowerlimit,
                            params=['thermstat_setting'],
                            vreturn='lower_limit',
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
          'led_BLUE':      Map( wrap=None,
                            target=led.set,
                            params=[led.BLUE],
                            vreturn=None,
                            chain='led_status'),
          'led_status':   Map( wrap=a_get('get_state'),  # @properties must be wrapped
                            target=None,
                            params=[led],
                            vreturn='led_state',
                            chain=None)
                        }

    _read_keys = ['get_temp', 'update_temp_hist', 'update_fan_hist', 'fan_overheating', ]

    _local_values = { 'fan': fan, 'led': led, 'switch': switch }

    _transforms =  {'get_temp': calibrate_temp }

    def __init__(self,
                 values:VolatileDict=None):

        super().__init__(values=values)


if __name__ == '__main__':

    if mem_free_avail:
        start_main_mem = mem_free()

    DEBUG = False

    # to guarantee order in mpy, only use list of k/v tuple pairs, not dict
    vd = VolatileDict([('room_temp',10.1),
                      ('temp_history', [ 0.0, 0.0, 0.0, 0.0 ]),
                      ('upper_limit', 35.5),
                      ('lower_limit', 34.5 ),

                      ('fan_ON', Fan.ON),
                      ('fan_OFF', Fan.OFF),
                      ('fan_SUSPEND', CheapFan.SUSPEND),
                      ('fan_UNSUSPEND', CheapFan.UNSUSPEND),
                      ('fan_state', Fan.OFF),
                      ('fan_overheated', False),

                      ('switch_ON', Switch.ON),
                      ('switch_OFF', Switch.OFF),
                      ('switch_state', Switch.OFF),

                      ('thermstat_setting', 35.0),

                      ('led_state', (LED.RED, LED.ON)),
                      ('led_off_param', {'brightness': led.OFF}),  # dict keywords, not list

                      ])

    vd.read_only.extend(['fan_ON', 'fan_OFF', 'fan_SUSPEND', 'fan_UNSUSPEND', 'switch_ON',
                           'switch_OFF', 'led_off_param'])  # constants

    print()
    print('### Fan IOMapper Prototype ###')
    print()

    iom = FanIOM(values=vd)  # override default _values
    
    del(vd)

    print()
    print('### Starting IOMapper Run ###')
    print()

    # read_keys = ['get_temp', 'update_temp_hist', 'update_fan_hist', 'fan_overheating', ]

    def run_cycle():

        iom.values.reset()

        iom.read_into_values()  # using iom defined read_keys.

        print('Updated value dict: ', iom.values)
        print()
        actions = []

        if DEBUG: print('Keys changed:  ', iom.values.keys_changed(), '\n')
        
        # Implementation of Fan Mapper logic, state transitions 

        vd = iom.values  # values dict

        if vd['fan_overheated'] == True:
            if vd['fan_state'] == vd['fan_ON']:
                iom.write('fan_suspend')

        else:   # normal operation

            if vd['fan_state'] == vd['fan_SUSPEND']:

                iom.write('fan_unsuspend')

            elif vd['fan_state'] == vd['fan_OFF']:
                if (vd['room_temp'] > vd['upper_limit'] or
                   vd['switch_state'] == vd['switch_ON']):

                    iom.write('fan_on')

            elif vd['fan_state'] == vd['fan_ON']:
                if vd['switch_state'] == vd['switch_OFF']:
                    if vd['room_temp'] < vd['lower_limit']:

                        iom.write('fan_off')
            else:
                pass # debugging, no action


    def erun(iom, limit):

        n = 1

        print('... using fan object: ', iom.values['fan'])
        print()

        fanref = iom.values['fan']

        while n <= limit:

            print('Running cycle: ', n)
            print()

            if n==4:
                print('-> Setting switch_on')
                iom.write('switch_on')
                print()

            if n==8:
                print('-> Setting switch_off')
                iom.write('switch_off')
                print('-> Setting thermostat to 34 ')
                iom.values['thermstat_setting'] = 34.0
                iom.write('thermstat_reset')
                print()

            run_cycle()

            print('fan state:         ', ['off', 'on', 'suspended'][fanref.state])
            print('fan history:       ', fanref.state_history)
            print('fan internal_temp: ', round(fanref.internal_temp, 2))
            print('keys changed:      ', iom.values.keys_changed())
            print()
            
            
            n += 1

    erun(iom, 16)



    print()
    print('### End run ')
    print('Values dict ->')

    checkstats(iom.values)

    # print(locals())

    if mem_free_avail:
        print('Memory Usage')
        print('Start mem free:           ', start_mem )
        print('Start mem alloc:          ', start_memalloc )
        print('Free/Usage start __main__:', start_main_mem, '/', start_mem - start_main_mem)
        print('Free/Usage end __main__ : ', mem_free(), '/', start_mem - mem_free())
        collect()
        print('Free/Usage (collected):   ', mem_free(), '/', start_mem - mem_free())
        print('Mem Alloc:                ', mem_alloc(), ' ')

""""
Arduino ESP32
Memory Usage ( 1.22 )
Start mem free:            8196496
Start mem alloc:           57968
Free/Usage start __main__: 8192544 / 3952
Free/Usage end __main__ :  8133488 / 63008 (diff ?)
Free/Usage (collected):    8199872 / -3376
Mem Alloc:                 54592

RP2040  ( 1.23 )
Memory Usage
Start mem free:            117312
Start mem alloc:           74112
Free/Usage start __main__: 113360 / 3952
Free/Usage end __main__ :  102480 / 14832
Free/Usage (collected):    120784 / -3472
Mem Alloc:                 70640

Note: number above after a few runs.  Mem alloc may be more reliable/stable
overall, but will total_mem - mem_alloc always = free mem ?  Doesn't look
like it, so numbers ( and definitions ? ) are approximate.

"""





