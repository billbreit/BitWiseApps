"""Demo of IOEngine

module:     fanengine
version:    v0.0.2
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

The Fan Engine is an extended example of IOEngine, a process engine (driver)
for a defined IOMap and IOMapper.  The map is from action keywords to
objects methods or APIs of imaginary devices, programs or protocols.  the IOMap
and conditions defined in the IOEngine simulates the design for a simple ( and
inexpensive ! ) fan with some non-simple logic requirements.


"""

import sys

def is_micropython():
    """Test for mpy,  JSON or MRO bugs """  
    return sys.implementation.name == 'micropython'

try:
    from gc import mem_free, mem_alloc, collect
    mem_free_avail = True
    collect()  # seems to make a difference. why ?
    start_mem = mem_free()
    start_memalloc = mem_alloc()
except ImportError:
    mem_free_avail = False

# from random import random

from lib.evaluator import Evaluator, Condition
from lib.vdict import VolatileDict, checkstats

from iomapper import IOMapper, Map, MDEBUG, MM, SetVal, Run
import iomapper

import ioengine
from ioengine import  CMacro, RuleSetLoader, EDEBUG


EDEBUG = True  # for code debugging and action/condition debugging
# EDEBUG = False  # for code debugging and action/condition debugging
# iomapper.EDEBUG = True

from fan_mapper import CheapFanIOMapper




### Stub Classes/Functions for convenience,
### device subclasses, or odd interfaces.





if __name__ == '__main__':

    print()
    print("""IOEngine Demo of a Remarkably Unreliable Fan""")
    print()
    print('Due bad ( management ) decisions and poor component quality, the')
    print('fan burns out at 42 degrees, usually during a hot spell. The objective')
    print('is to keep the fan going without the fan.interal_temp > 42C.\n ')
    print("Not always successfully ... ")
    print()

    if mem_free_avail:
        start_main_mem = mem_free()

    EDEBUG = True
    # EDEBUG = False

    print('### Fan IOEngine Prototype ###')
    print()

    iom = CheapFanIOMapper()   # use default _values

    conditions = { 'fan_suspend':
                     [Condition('fan_overheated', 'eq', True ),
                     Condition('fan_state', 'eq', 'fan_ON' )],

                'fan_unsuspend':
                    [Condition('fan_overheated', 'eq', False ),
                    Condition('fan_state', 'eq', 'fan_SUSPEND' )],

                'fan_on' : [
                    [CMacro('normal_off'),  # conds expanded in __init__
                     Condition('room_temp', 'gt', 'upper_limit')],
                   # OR
                    [CMacro('normal_off'),
                     Condition('switch_state', 'eq', 'switch_ON')]],

                'fan_off':
                     [CMacro('normal_on'),
                     Condition('switch_state', 'eq', 'switch_OFF'),
                     Condition('room_temp', 'lt', 'lower_limit')]
              }

    dcmacros = { 'normal_off': [Condition('fan_overheated', 'eq', False ),
                                Condition('fan_state', 'eq', 'fan_OFF' )],
                'normal_on'  : [Condition('fan_overheated', 'eq', False),
                                Condition('fan_state', 'eq', 'fan_ON')]
                }
    conflist = ['fan_state', {'switch_on', 'switch_off'}]


    read_keys = ['get_temp', 'update_temp_hist', 'update_fan_hist', 'fan_overheating', ]

    #'''
    ioeng = ioengine.TransactorEngine(iom, conditions=conditions, readkeys=read_keys,
                                cmacros=dcmacros, conflict_sets=conflist )
    #'''
    '''                            
    ioeng = ioengine.MonitorEngine(iom, conditions=conditions, readkeys=read_keys,
                                cmacros=dcmacros, conflict_sets=conflist )
    '''
    
    checkstats(iom.values)
    print()

    print('### Starting Fan IOEngine Run ###')
    print()

    def erun(ioengn, limit):

        n = 1

        print('... using fan object: ', ioengn.values['fan'])
        print()

        fanref = ioengn.values['fan']

        while n <= limit:

            print('Running cycle: ', n)
            print()

            ioengn.run_cycle()

            if n==4:
                print('--> Injecting switch_on into agenda')
                ioengn.add_agenda(Run('switch_on'))
                print()

            if n==8:
                print('--> Injecting switch_off into agenda')
                ioengn.add_agenda(Run('switch_off'))
                print('--> Injecting set thermostat to 34 and thermstat_reset.')
                ioengn.add_agenda([SetVal('thermstat_setting', 34.0),
                                   Run('thermstat_reset')])
                print()

            print('room temp:         ', ioengn.values['room_temp'])
            print('fan state:         ', ['off', 'on', 'suspended'][fanref.state])
            print('fan history:       ', fanref.state_history)
            print('fan internal_temp: ', round(fanref.internal_temp, 2))
            print('switch state:      ', ['off', 'on'][ioengn.values['switch_state']])
            print('agenda:            ', ioengn.agenda )
            print()

            n += 1

    run_times = 16

    erun(ioeng, run_times)

    print()

    print(f'Values dict at the end of {run_times} cycles \n')
    print(ioeng.values)
    print()
    print('=== End ioeng.run ===')
    print()

    print('=== Test save to/load from json file === \n')
    print('Save IOEng.to_dict -> JSON file')
    print('Load JSON file and restore types -> IOEng.load_from dict')
    print('via the RuleSetLoader.')
    print()

    class FanRuleSetLoader(RuleSetLoader):

        _def_iomappers = { 'CheapFanIOMapper': CheapFanIOMapper }

        def __init__(self, *args, **kws ):

            super().__init__( *args, **kws )

    ioedict = ioeng.to_dict()
    print('ioedict.to_dict:  ')
    # print(ioedict)
    print()
    print('--> Creating RuleSetLoader \n')
    loader = FanRuleSetLoader()
    filename = 'fan_engine'
    loader.save(ioedict, filename)
    print(f"--> Saved ioe_dict to json in '{loader.default_filename}' \n")
    
    if is_micropython():
        print()
        print('At this point, MicroPython will cause a JSON exception.  Maybe MRO ?')
        print("Sorry bout that - it's been a very persistent bug, still working on it.")
        print()

    print('--> Loading from json file and restoring types\n')
    from_dict = loader.load(filename)

    print('Original dict == Restored dict ---> ', ioedict == from_dict)
    print()

    if ioedict != from_dict:
        print('Checking for diffs ')
        for k, v in ioedict.items():
            if v != from_dict[k]:
                print('key: ', k )
                print('orig:    ', v)
                print('restored:', from_dict[k])


    print('--> Deleting ioeng instance \n')
    del(ioeng)

    EDEBUG = True
    # EDEBUG = False

    print('--> Creating new instance of ioengine from dict \n')
    ioeng2 =  ioengine.TransactorEngine(iom, Evaluator, from_dict=from_dict )
    # ioeng2 =  ioengine.MonitorEngine(iom, Evaluator, from_dict=from_dict )

    print(f'Values dict, with same values as the end of {run_times} cycle,')
    print(f'plus one cycle, cycle {run_times+1} as it were.')
    print()

    print(ioeng2.values)

    ioeng2.EDEBUG = True

    print('Run 3 cycles to see if the engine works \n')
    print('Note that the engine is using a still-stateful value dict and')
    print('and the engine must run dangling agenda from the previous')
    print('cycle in order to to maintain logical consistency.')
    print()

    erun(ioeng2, 3)

    print()
    print('=== End of Save/Load from File Test ===')
    print()



    # checkstats(iom.values)
    # print()
    # print('dir ioeng ', dir(ioeng2))

    # print('locals: \n')
    # print(locals())
    # print()

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
The Mysteries of Memory Management

ESP32
Memory Usage ( 1.22 )
Start mem free:            8191376
Free/Usage start __main__: 8187472 / 3904
Free/Usage end __main__ :  8152912 / 38464
Free/Usage (collected):    8194224 / -2848
Mem Alloc:                 60240

RP2040  ( 1.23 )
Memory Usage ( earlier in dev. )
Start mem free:            131888
Start mem alloc:           59536
Free/Usage start __main__: 127936 / 3952
Free/Usage end __main__ :  92656 / 39232
Free/Usage (collected):    135248 / -3360
Mem Alloc:                 56176

Memory Usage ( later in dev. )
Start mem free:            178800  ???
Start mem alloc:           12624   ???
Free/Usage start __main__: 73872 / 104928
Free/Usage end __main__ :  132160 / 46640
Free/Usage (collected):    132896 / 45904
Mem Alloc:                 58528

???  must have been gc uncollectables in earlier version

Compare to fan_example.py, same basic functions without IOEngine

Memory Usage
Start mem free:            179616
Start mem alloc:           11808
Free/Usage start __main__: 112320 / 67296
Free/Usage end __main__ :  136832 / 42784
Free/Usage (collected):    149984 / 29632
Mem Alloc:                 41440

THe meme diff is 17K, significant,  also runs much faster.


Note: number above after a few runs.  Mem alloc may be more reliable/stable
overall, but will total_mem - mem_alloc = free mem ?  Doesn't look like it.
For instance, numbers imply 256K - 55K = 201K free at start.  Actual is
256K - 143K = 132K free, so 143K total is allocated ( or at least not
counted as free ). 80K system, 60K user memory allocated ?  Or is
actual user mem usage 40K, as above ?

ESP32 first run - collected at start mem (?)
Memory Usage
Start mem free:            8301360
Free/Usage start __main__: 8157952 / 143408
Free/Usage end __main__ :  8191648 / 109712
Free/Usage (collected):    8193904 / 107456
Mem Alloc:                 60560
"""





