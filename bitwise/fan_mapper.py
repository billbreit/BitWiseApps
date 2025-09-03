""" IOMapper Def """

from random import random

from iomapper import IOMapper, Map, MDEBUG, MM

from lib.vdict import VolatileDict, RO, checkstats
from lib.core.functools import partial
from lib.core.getset import i_get, i_set, a_get, a_set

from idevices import Fan, LED, RandomThermometer, Thermostat, Switch


led = LED()
thermstat = Thermostat()
switch = Switch()
fan = Fan()

### Function helpers
### Stub Classes/Functions for convenience,
### device subclasses, or odd interfaces.

def temperature():
    return round(21 + ( 4 - 5*random()),2)

def calibrate_temp(t:float, factor:float=1.0) -> float:
    return round(t * factor,2)

def get_upperlimit(temp:float):

    return temp + 0.5

def get_lowerlimit(temp:float):

    return temp - 0.5



### Basic Fan Example ###


class BasicFanIOMapper( IOMapper ):

    _values = VolatileDict([('room_temp',10.1),
                      ('fan_ON', Fan.ON),
                      ('fan_OFF', fan.OFF),
                      ('fan_state', Fan.OFF),
                      ('switch_ON', Switch.ON),
                      ('switch_OFF', Switch.OFF),
                      ('switch_state', Switch.OFF),
                      ('led_state', (LED.RED, LED.ON)),
                      ('led_off_param', {'brightness': LED.OFF}),
                      ('upper_limit', 35.5),
                      ('lower_limit', 34.5 ),
                      ]) # list of k/v tuple pairs

    _iomap = {'get_temp': MM( target=temperature,    # MakeMap helper
                             vreturn='room_temp'),

              'fan_on':   MM( target=partial(fan.set_state,verbose=True),
                             params=['fan_ON'],
                             chain=['fan_status', 'led_GREEN']),
              'fan_off':  MM( target=partial(fan.set_state,verbose=True),
                             params=['fan_OFF'],
                             chain=['fan_status', 'led_RED']),
              'fan_status': MM( target=fan.get_state,
                             vreturn='fan_state'),

              'switch_on':  MM( target=switch.set_state,
                             params=['switch_ON'],
                             chain=['switch_status']),
              'switch_off':  MM( target=switch.set_state,
                             params=['switch_OFF'],
                             chain=['switch_status']),
              'switch_status': MM( target=switch.get_state,
                               vreturn='switch_state'),

              'led_on':    MM( target=led.set,
                             params=[None, led.ON],  # need positional None
                             chain='led_status'),
              'led_off':   MM( target=led.set,
                             # or params='led_off_param',
                             params={'brightness': led.OFF}, # keywords, dict not list
                             chain='led_status'),
              'led_RED':   MM( target=led.set,
                             params=[led.RED],
                             chain='led_status'),
              'led_GREEN': MM( target=led.set,
                             params=[led.GREEN],
                            chain='led_status'),
             'led_BLUE':  MM( target=led.set,
                             params=[led.BLUE],
                             chain='led_status'),
             'led_status': MM( wrap=a_get('get_state'),  # @properties must be wrapped
                             params=[led],
                             vreturn='led_state')
                        }

    _read_keys = ['get_temp']

    _local_valuest = { 'fan': fan, 'led': led, 'switch': switch }

    _transforms =  {'get_temp': partial(calibrate_temp, factor=1.6)}
    
    def __init__(self,
                 values:VolatileDict=None):

        super().__init__(values=values)
    



### Cheap Fan Example ###

### Stubs, helpers

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

class DeadFanException(Exception):

    pass

class CheapFan(Fan):
    """The Boss, in his wisdom, has decided use really cheap fans,
        which overheat when the internal temp is over 42.0 C ( or
        whataver ) and that destroys the fan.  A fix cheaper
        than a thousand cheap fans ... now, how to deep six those
        pesky Customer Satisfaction Questionnaires ?

    """

    SUSPEND:int = 2
    UNSUSPEND:int = 3
    MAXTEMP:float = 40.0
    DEADFAN:float = 42.0

    heat_index = 1.7  # degree gain per cycle, by type of fan

    def __init__(self,*args, **kwargs):

        super().__init__(self, *args, **kwargs )

        self.state_history = [ 0, 0, 0]
        self.internal_temp = 0.0
        self.saved_state = self.OFF


    def overheating(self, temp_hist:list):
        """Estimated internal temp from tests/heuristics"""

        self.internal_temp = sum(temp_hist)/len(temp_hist) + sum(self.state_history) * self.heat_index

        if self.internal_temp > self.DEADFAN:
            raise DeadFanException(f'DEAD FAN ! Internal temp/history -> {self.internal_temp} / {temp_hist}')

        return self.internal_temp > self.MAXTEMP

    def set_state(self, new_state:int, verbose:bool=False ):

        if new_state == self.SUSPEND:
            if verbose:
                print('Fan -> overheating, fan SUSPEND')

            self.saved_state = self.state
            self.state = new_state

        else:
            if new_state == self.UNSUSPEND:
                if verbose:
                    print('Fan -> UNSUSPEND, restoring fan state -> ', self.saved_state)
                    # print('Fan -> UNSUSPEND, restoring fan state -> ', self.OFF)
                new_state = self.saved_state  # saved is always ON
                # new_state = self.OFF   # big diff !!!  3-4x less dead fans
            # potentially overriding partial
            super().set_state(new_state, verbose)

    def update_history(self):

        if self.state==self.ON:
            self.state_history.append(1)
        else:
            # state = OFF or SUSPEND
            self.state_history.append(0)

        self.state_history.pop(0)

cfan = CheapFan()



class  CheapFanIOMapper(IOMapper):
    """ Class variables are passed to IOMapper __init__

        Action key / Map to 'external' object (often wrapped) or function

        params: a list of key name of values in the values dict, whcih is
        also 'external' to both the IOMapper and the IOEngine.

        vreturn: updates a key/value in the values dict.

        chain: the next actions to trigger, *unconditionally*, whenever
        'this action' then 'that list of actions'. Condtional actions
        are defined in the IOEngine.

    """

    # to guarantee order in mpy, must use list of k/v tuple pairs, not dict
    _values = VolatileDict([
                      ('room_temp',10.1),
                      ('temp_history', [ 0.0, 0.0, 0.0, 0.0 ]),
                      ('upper_limit', 35.5),
                      ('lower_limit', 34.5 ),

                      RO('fan_ON', Fan.ON),
                      RO('fan_OFF', Fan.OFF),
                      RO('fan_SUSPEND', CheapFan.SUSPEND),
                      RO('fan_UNSUSPEND', CheapFan.UNSUSPEND),
                      ('fan_state', Fan.OFF),
                      ('fan_overheated', False),

                      RO('switch_ON', Switch.ON),
                      RO('switch_OFF', Switch.OFF),
                      ('switch_state', Switch.OFF),

                      ('thermstat_setting', 35.0),

                      ('led_state', (LED.RED, LED.ON)),
                      RO('led_off_param', {'brightness': led.OFF}),  # keywords, dict not list
                      ])

    _iomap = {'get_temp': MM( target=temperature,
                              vreturn='room_temp',
                              # chain=['update_temp_hist']),  # not working ?
                              chain=[]),
         'update_temp_hist': MM( target=update_temp_hist,
                                 params=['temp_history', 'room_temp'],
                                 vreturn='temp_history'),

         'fan_on':       MM( target=partial(cfan.set_state,verbose=True),
                             params=['fan_ON'],
                             chain=['fan_status', 'led_GREEN']),
         'fan_off':      MM( target=partial(cfan.set_state,verbose=True),
                             params=['fan_OFF'],
                             chain=['fan_status', 'led_RED']),
         'fan_suspend':  MM( target=partial(cfan.set_state,verbose=True),
                             params=['fan_SUSPEND'],
                             chain=['fan_status', 'led_BLUE']),
         'fan_unsuspend': MM( target=partial(cfan.set_state,verbose=True),
                              params=['fan_UNSUSPEND'],
                              chain=['fan_status']),
         'fan_status':   MM( target=cfan.get_state,
                             vreturn='fan_state'),
         'fan_overheating': MM( target=cfan.overheating,
                                 params=['temp_history'],  # room_temp bound above
                                 vreturn='fan_overheated'),
         'update_fan_hist': MM( target=cfan.update_history),

         'switch_on':   MM( target=switch.set_state,
                            params=['switch_ON'],
                            chain=['switch_status']),
         'switch_off':  MM( target=switch.set_state,
                            params=['switch_OFF'],
                            chain=['switch_status']),
         'switch_status': MM( target=switch.get_state,
                              vreturn='switch_state'),

         'thermstat_get' : MM( target=thermstat.get_setting,
                            vreturn='thermstat_setting'),
       'thermstat_reset' : MM( target=thermstat.reset,
                               params=['thermstat_setting'],
                               chain=['set_upperlimit', 'set_lowerlimit']),
         'set_upperlimit': MM( target=get_upperlimit,
                            params=['thermstat_setting'],
                            vreturn='upper_limit'),
         'set_lowerlimit': MM( target=get_lowerlimit,
                               params=['thermstat_setting'],
                               vreturn='lower_limit'),

          'led_on':       MM( target=led.set,
                               params=[None, led.ON],  # need positional None
                            chain='led_status'),
          'led_off':      MM( target=led.set,
                              # params='led_off_param',
                              params={'brightness': led.OFF}, # keywords, dict not list
                             chain='led_status'),
          'led_RED':      MM( target=led.set,
                              params=[led.RED],
                              chain='led_status'),
          'led_GREEN':    MM( target=led.set,
                              params=[led.GREEN],
                              chain='led_status'),
          'led_BLUE':     MM( target=led.set,
                              params=[led.BLUE],
                              chain='led_status'),
          'led_status':   MM( wrap=a_get('get_state'),  # @properties must be wrapped
                              params=[led],
                              vreturn='led_state')
                        }

    _read_keys = ['get_temp', 'update_temp_hist', 'update_fan_hist', 'fan_overheating', ]

    _local_values = { 'fan': cfan, 'led': led, 'switch': switch }

    _transforms =  {'get_temp': partial(calibrate_temp, factor=1.6)}

    def __init__(self,
                 values:VolatileDict=None):

        super().__init__(values=values)


