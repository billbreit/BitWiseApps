"""Demo of IOEngine

module:     fan_monitor demo
version:    v0.0.2
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

The Fan Monitor is an extended example of MonitorEngine, a process engine (driver)
for a defined IOMap and IOMapper that detect changed in values and only tests actions
that may have changed.

Event ( Changed value keys ) -> used by -> Conditions -> used by Actions.

* Find changed keys.
* Test potentially changed condtions for changed evals ( True->False, False->True ).
* Find action triggers using the changed condtions and test for trigger of action.  

The map is from action keywords to objects methods or APIs of imaginary devices,
programs or protocols.

This demo uses values conditions defined in the IOEngine to simulats the design for
a simple ( and unreliable ! ) fan with some non-simple logic requirements.

"""

import sys

from lib.core.utils import is_micropython

try:
    from gc import mem_free, mem_alloc, collect
    mem_free_avail = True
    collect()  # seems to make a difference. why ?
    start_mem = mem_free()
    start_memalloc = mem_alloc()
except ImportError:
    mem_free_avail = False


from lib.evaluator import Evaluator, Condition
from lib.vdict import VolatileDict, checkstats


from iomapper import IOMapper, Map, MDEBUG, MM, SetVal, Run
import iomapper


from ioengine import  CMacro, RuleSetLoader, MonitorEngine
import ioengine



# ioengine.EDEBUG = False  # for code debugging and action/condition debugging
ioengine.EDEBUG = True  # for code debugging and action/condition debugging

saved_actions = 0   # action tests saved by using monitor alg vs. transactor, kludgy

from fan_mapper import CheapFanIOMapper, DeadFanException
import fan_mapper



### Usually stub classes or functions for convenience,
### device subclasses, or odd interfaces.  See fan_mapper.py

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


    ioeng = MonitorEngine(iom, conditions=conditions, readkeys=read_keys,
                                cmacros=dcmacros, conflict_sets=conflist )

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
            
            try:
                ioengn.run_cycle()
            except DeadFanException as d:
                print()
                print('### Fan burned out !!! ###')
                print(d)
                print('Try to restore correct monitor ruleset for CheapFan')
                print('from saved JSON rules ... and run it again. \n')
                fan_mapper.cfan = fan_mapper.CheapFan()
                return

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

    cycles = 16

    erun(ioeng, cycles)

    print()

    print(f'Values dict at the end of {cycles} cycles \n')
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
    print('ioeng.to_dict:  ')
    # print(ioedict)
    
    print('--> Deleting ioeng instance \n')
    del(ioeng)

    print()
    print('--> Creating RuleSetLoader \n')
    loader = FanRuleSetLoader()
    filename = 'fan_monitor'
    
    loader.save(ioedict, filename)
    
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


    EDEBUG = True
    # EDEBUG = False

    print('--> Creating new instance of ioengine from dict \n')
    ioeng2 =  MonitorEngine(iom, Evaluator, from_dict=from_dict )

    print(f'Values dict, with same values as the end of {cycles} cycle,')
    print(f'plus one cycle, cycle {cycles+1} as it were.')
    print()

    print(ioeng2.values)

    ioeng2.EDEBUG = True

    print('Run 3 cycles to see if the engine works \n')
    print('Note that the engine is using a still-stateful value dict and')
    print('and the engine must run dangling agenda from the previous')
    print('cycle in order to to maintain logical consistency.')
    print()
    
    cycles = 3

    erun(ioeng2, 3)
    
    print()
    
    print('=== End of Save/Load from File Test ===')
    print()
    
    del(ioeng2)

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

