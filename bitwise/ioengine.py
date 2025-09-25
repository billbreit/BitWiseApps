"""
module:     ioengine
version:    v0.0.3
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2025 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

IOEngine is a prototype of a process engine (driver) for an IOMap.

IOEngine is a state-transition engine (driver) for the actions definied in
an IOMap.  IOEngine drives an IOMap, like a multi-step process engine.

THe basic flow is from a values dictionary binding to evaluaions of conditions using
the values to actions using the condtions as triggers to perform the action.

Keys ( in values dict )  - used in ->  Conditions  - used in ->  Action Triggers

Forward mapping also allows for backward mapping, such as when testing/binding
changed conditions to their their changed values.

Keys ( in values dict )  <- use -  Conditions  <- use -  Action Triggers

However, the cross-references for forward/backward mapping between
Keys-Conditions-Actions ( 'xrefs' ) consumes a significant amount of memory,
maybe 40K and up.  The small demos will run on a 256K microcontroller, less
80K heap anda 30K reserve for in extrema memory, leaving roughly 150K of
actual usable memory.

Subtract another couple dozen K for device imports and supporting code, plus
a DataStore instance ( a 15K import + maybe 40K of data ) and then add another
40K for IOMappe/IOEngine instances and xrefs, memory gets rather tight.

A Pico 2 with a staggering 512K of memory !?
Reporting 420K free, maybe equiv. to 380K usable with lazy gc / heap creep ?

Note current demo save/restore ruleset won't run on micropython !!!

"""

from collections import namedtuple

import sys

def is_micropython():
    """Test for mpy,  JSON or MRO bugs """  
    return sys.implementation.name == 'micropython'


from iomapper import IOMapper, Map, MM, SetVal, Run
import iomapper

from lib.core.gentools import chain
from lib.core.bitops import power2, bit_indexes, more_than_one_bit_set
from lib.core.bitops import bitslice_set
from lib.core.fsutils import JSONFileLoader

from lib.evaluator import Evaluator, Condition
from lib.tablestore import TableStore  # will be subclass RuleStore ?

from lib.vdict import VolatileDict, checkstats

# Important: debugging is set up as a visible engine demo generating a
# massive amount of output. Set scrollback to 1000 to play it safe.
# Reminder, 'clear' on Linux, 'cls' on Windows.

EDEBUG = True      # both code debugging and action/condition debugging
# EDEBUG = False   # both code debugging and action/condition debugging


class IOEngineError(Exception):
    pass

class RuleSetLoader(JSONFileLoader):
    """Load/save a rule set from a json file.
       Must create file with full Monitor type xrefs.
       Transactor uses a subset  """

    # override class defaults
    _def_dir = 'rulesets'
    _def_filename = 'ioenginetest'
    # _def_extention = 'json'

    _def_iomappers = { 'IOMapper': IOMapper }
    _def_evaluators = { 'Evaluator': Evaluator }

    def __init__(self, iomappers:dict=None, evaluators:dict=None, *args, **kws,  ):
        """fdir: str = None,
           filename: str = None,
           ext: str = None"""

        super().__init__(*args, **kws )
        
        self.iomapper:dict = self._def_iomappers
        self.evaluator:dict = self._def_evaluators
        
        print('in init ' , self.iomapper) 
        
        if iomappers:
            self.iomapper.update(iomappers) 
        if evaluators:
            self.evaluator.update(evaluators)
         

    def prepare_types(self, rs_dict:dict) -> dict:
        """Prepare non-jasonable types for save."""

        new_dict = {}
        new_dict.update(rs_dict)  # copy

        new_dict['conflict_sets'] = [list(s) for s in rs_dict['conflict_sets']]

        new_dict['mapper'] = rs_dict['mapper'] .__class__.__name__  # str, not ref
        new_dict['evaluator'] = rs_dict['evaluator'].__class__.__name__

        return new_dict


    def restore_types(self, json_dict:dict) -> dict:
        """Restore iomapper, evaluator, sets, Condition namedtuples."""

        def restore_conditions():

            conditions: dict = json_dict['conditions']
            new_cond_dict = dict()

            for k, v in conditions.items():

                new_conds = []
                for conds in v:
                    new_list = []
                    if isinstance(conds[0], list ):
                        new_list = []
                        for cond in conds:
                            new_list.append(Condition(*cond))
                        new_conds.append(new_list)
                    else:
                        new_conds.append(Condition(*conds))

                new_cond_dict[k] = new_conds

            return new_cond_dict

        new_dict = {}
        new_dict.update(json_dict)  # copy

        # new instances, may be overridden in ioe.load_from_dict
        new_dict['mapper'] = self.iomapper[new_dict['mapper']]()
        new_dict['evaluator'] = self.evaluator[new_dict['evaluator']]()

        new_dict['action_trigger_xref'] = [( a, t ) for a, t in new_dict['action_trigger_xref']]

        for k, conds in new_dict['cond_macros'].items():
            conds_list = []  # [ Condition(*cond) for cond in conds ]
            for cond in conds:
                conds_list.append(Condition(*cond))

            new_dict['cond_macros'][k] = conds_list

        new_dict['conditions'] = restore_conditions()
        new_dict['conflict_sets'] = [ set(s) for s in json_dict['conflict_sets']]
        new_dict['condition_set'] = [Condition(*cond) for cond in json_dict['condition_set']]

        return new_dict


"""May need to extend mappings IOEngineDef for evaluator class."""

class IOEngineFactory(object):
    """Engine customizations based on use-case senarios:
        1 - monitor type, fan example, run() loop
        2 - transactional type, may not be appropriate at io level.  might boil
            down to populated static values dict with a few volatile items,
             ex. 'customer' and 'customer order' from iomapper.
        3 - messaging type, TBD. There might be IO queues driving it.

        Needs to be some sort of 'routine' conflict detection and
        exception handling/logging capability as a build parameter.

        The IO Engine factory may be invoked by a 'Process Engine'.  The
        Process Engine might be mediating/juggling between different ioengines.

        The IO Engine factory might have multipe iomappers in a NamedDict
        namespace, ex. IF 's1.temp' > 's1.temp_max' AND
                          's2.temp' > 's2.temp_max'
                       THEN 'this_is_bad_do_something'

        s1 = {'temp':123,
              'temp_max': 100 } in namespace 's1'

        s2 = {'temp':94,
              'temp_max': 95 } in namespace 's2'

        Probably needs a local namespace, for ex. 'loc.number_of_fans_overheating'

        Ways to build

        *  python defined iomapper, conditions, etc defs passed as params
           to class at _build time.

        *  python defined IOEngineDef passed as params to class ( *IOEngineDef ).

        *  json file definition of IOEngine rule set, with new instances of
           IOMapper and Evaluator, something like:

           IOEngine( from_dict = ioeng.from_dict( json_file_loader.load )).

        *  json file definition of IOEngine  rule, with existing instances
           of IOMapper and Evaluator that is:

           IOEngine( iomap, evaluator, from_dict = ioeng.from_dict( json_file_loader.load )).
           Note that the iom.values_dict will have state, whatever values it last had at
           the end of the last ruleset load/run.  This might be a ruleset sequence,
           like Order_validate        ->
                Order_checkstock      ->
                Order_checkcredit     ->
                Order_apply_discounts ->
                etc.

    """

    pass

""" ### IOEngineDef ###

    iomapper:IOMapper or subclass
    evaluator: Evaluator or subclass
    conditions: dict[ str, 'List' ]
                  in form - 'action':list[Condition] or    # single trigger
                            'action':list[list[Condition]] # multiple OR triggers
    readkeys: list[str] - override readkeys in IOMapper.
    cmacros: dict[str,list[Condition] - a condition macro replaces itself with
                                        a set of repetitive conditions.
    conflict_sets: list[str|set[str]] - string mean 'conflict key', gets expanded
                                        into set[action keys]
    from_dict :dict - a IOEngine instances defined in a dictionary, possibly
                      restored from a json file. opposite of to_dict.
    debugging; boolean - for debugging rulebase, not yet used,

"""

# no namedtuple._fields in mpy
ioenames = [ 'iomapper',
             'evaluator',
             'conditions',
             'readkeys',
             'cmacros',
             'conflict_sets',
             'from_dict',
             'debugging']

IOEngineDef = namedtuple('IOEngineDef', ioenames)

# Action Def for:
#  name: str - action key, default Run('action') unless overriden in script.
#  conditions / trigger conditions: list[Cond]|list[list[Cond]]
#  script:list[SetVal|Run] -  list of script command, overrides Run('action') .

ActionDef = namedtuple( 'ActionDef', ['name', 'conditions', 'script'])



# Commands for the agenda mechanism, pass actions forward to next binding cycle

# SetVal = namedtuple('SetVal', ['key', 'value'])  # value needs indirection
# Run = namedtuple('Run', ['action'])    # params override ?

# Common name for repeating set of conditions.  Lookup name in cmarcos dict
# and expand into lists of conditions that get built into action_trigger_xref.
# __init__ param self.cmacros: dict[str, list[Condition]]

CMacro = namedtuple('CMacro', ['name'])  # used in list of conditions.

cm = CMacro('testing')


class IOEngineBase():

    """

    Keys in the values dict - used in ->  Conditions - used in -> Action Triggers.
    The 'event' is a changed value in the values dict.

    Forward mapping and back mapping are both useful.

    Prototype - may need refactoring, more like a factory, where ECA in an IOEngineDef.
       Can this even be subclassed, more like sequence of function wrappers ?, will
       need many more parameters for handling customizations from ioengine factory.

       ### Engine Definition, External Structre

       mapper: IOMapper  - mapping external functions calls, either afferent or efferent.

       mapper has mapper.values:  VolitaleDict - source of all values for IOEngine and mapper.

       evaluator: Evaluator - evaluates condition and returns T/F
 -
       conditions: dict[str,list['Conditions']]
          action keys with either List[Condition], simple AND list
                           or     List[List[Condtion]] OR list with embedded AND lists

       read_keys: list[str] - list of action keys in IOMapper for read_into_values,
          can read a subset of source values into the values dict rather than using
          the default read_keys defined in the IOMapper.  Could also be a 'side process'
          for minor binding cycles between major cycles.

       cond_macros:dict[str,list] - macros for sets of conditions for replacement
                             insetion into action triggers at *build time*.
                            Example: CMacro('name') ->{'name': [Condition*('a', 'eq', 'b'),
                                                                Condition*('b', 'eq', 'c')],
                                                        etc....
                                                      }
        conflict_sets: list[str|set[str]] - sets of conflicting action. Can use string as
               conflict key:str, generating a set of actions using the value key,
               ex. conflcit key 'device_state' -> { 'device_on', 'device_off' }

        from_dict: dict - create an engine from a dictionary create with to_dict,
              possibly saved and restored from a JSON file via RuleSetLoader.

        debugging: bool - tool to debug ruleset definition.  Not yet implemented.


        ### Internal Structures

        key_used: int -  a bit mask keys used in condtions mapped to vdict.vkeys
                         in order to AND with vdict.changed, keys changed and used.

        cond_evals: int - representing the evaluated state of the condition set ( and
                         FAPP, the state of the system ).
                         ex. 1110111011  - mapped to -> cond_set

        cond_keys: list - simple list of all occurances keys in the values dict used in a condition.

        condition_set: list[Condition] - calling this a set, but it is an sorted list of unique
                        conditions in an indexable list form.

        action_trigger_xref: list[tuple] - indexed to cond_set [('action', 0b00101), etc.].
             An action, trigger pair will appear for each OR construction defined
             in the condtions dictionary.

        key_conds_xref: dict - action, integer index to key usage in cond_set.
            Mainly for detecting conflicts in relations using 'eq', ex. device
            can not be both ON and OFF.  It represents XOR relational 'meta-rules'
            about condition/rule conflicts. There can be strategies for resolution
            of conflicts, ex. simple order of preference in a list, e.g. prefer ON to OFF.

        cond_trigger_xref: list[int] - mapping to -> action_triggers,
          detect potentially changed triggers to test, if match, add action to agenda.

          In principle, action conflicts should be eliminated with filtering conditions.

        See https://en.wikipedia.org/wiki/Rule-based_system
    """

    _export_attrs = ['mapper', 'evaluator', 'conditions', 'read_keys',
                     'cond_macros', 'conflict_sets', 'condition_set',
                     'action_trigger_xref', 'cond_actions_xref', 'key_conds_xref',
                     'cond_keys_xref', 'keys_used' ]

    def __init__(self,
                 mapper:IOMapper=None,
                 evaluator:Evaluator=None,
                 conditions:dict=None,
                 readkeys:list=None,
                 cmacros:dict = None,     # use kws
                 conflict_sets:list = None,  # list[str|set[str]]
                 from_dict:dict = None,
                 debugging:bool=False ):

        if EDEBUG:
            print('### Entering IOEngine __init__ ###')
            print()


            print('### IOMapper ')
            print()
            print('IOMapper.iomap: ')
            for k, v in mapper.iomap.items():
                print(f"{k:16}:  {v}")
                # print(f"  {v}")
            print()


            print('Initial Values Dict: ')
            print(mapper.values)
            print()
            print('local vals: ', mapper.local_vals)
            print()
            print('transforms:  ', mapper.transforms)
            print()

        if mapper.values is not None and isinstance(mapper.values, VolatileDict):
            self.values = mapper.values
        else:
            raise IOEngineError('Values Dict Empty: must provide VolatileDict with values.')

        self.evaluator = evaluator or Evaluator()  # if instance is None, default

        # usually default, may be overidden in from_dict construct
        self.evaluator = evaluator or Evaluator()  # usually default, maybe over

        # self.agenda = []

        # Test for from_dict, then do reload

        if from_dict:
            if EDEBUG:
                print('--> Initializing with ruleset dict.')
                # print('from dict ')
                # print(from_dict)
                print()
            self.load_from_dict(from_dict)
            if mapper:
                if EDEBUG:
                    print('--> Override mapper instance with ', mapper)
                    print()
                self.mapper = mapper # if mapper inst, override
            self.cond_evals = 0
            self.values.reset()
            if EDEBUG:
                print('--> IOEngine built from dictionary. ')
                print()
                # self.engine_info()
                print()
                print('### Exiting IOEngine __init__ ### \n')
                print()
            return

        self.mapper:IOMapper = mapper  # usually subclass

        # 'cycle driver' keys, action keys for the next read cycle,
        # more efficient than initalizier 'all vreturns' in iomapper.
        # Some action keys in the list may change or trigger objects
        # and not have vreturns.

        self.read_keys = readkeys or self.mapper.read_keys
        self.cond_macros = cmacros or {}


        # expand CMacro[name], rebuild conditions by key
        # dectect, lookup cmacros:dict[str, list[Conditions]]
        # if CMacro for condition, append

        ## conditions:list - list[Condition] or list[list[Condition]]]

        self.conditions: dict = self._expand_cmacros(conditions or {})

        # Start building internal structures

        # condition_set, sorted list of unique Condition( lhs, rel, rhs ) tuples.
        # Most xref structures map either to or from the unique
        # slot index of the Condition in the condition_set.

        self.condition_set: list[Condition] = self._build_cond_set()


        # action-to-cond(trigger) xref,when int matches current eval, do action

        self.action_trigger_xref:list[str, int] = self._build_action_trigger_xref()


        # self.cond_actions_xref: list[int] = self._build_cond_actions_xref()

        # simple list of all occurances keys in the values dict used in a condition.
        #  list[ ('value key', condition_slot:int), temporary


        # self.cond_keys: list[tuple] = self._build_cond_keys()

        # key_used - maps to vdict keys, used to AND with values_changed

        # self.keys_used:int = self._build_keys_used()

        # key-to-condition xref,
        # self.key_conds_xref: dict[str.int] = self._build_key_conds_xref()

        # condition-to-keys xref, Not used yet

        # self.cond_keys_xref:list = self._build_cond_keys_xref()

        self.conflict_sets = conflict_sets or []

        if self.conflict_sets:
            self.conflict_sets = self._build_conflict_sets()

                # if self.conflict_sets:
        #    self.conflict_sets:list[set] = self._build_conflict_sets()



        if EDEBUG:
            print('conflict_sets:  ( sets of conflicting actions )')
            for conf in self.conflict_sets:
                print(conf)
            if not self.conflict_sets:
                print([])
            print()

        '''
        if EDEBUG:
            used_changed = self.keys_used & self.values.changed
            print('Values used and changed: ', bin(used_changed), '-> bit_index values.changed.' )
            for index in bit_indexes(used_changed):
                key = self.values.vkeys[index]
                print(f'  {key}  {self.values[key]}')
            print()
        '''

        # cond_evals represents the effective state of the engine, changes can trigger actions
        self.cond_evals = 0  # eval true/false of conditions for values

        if EDEBUG: print('Reset initializations in values dict \n')

        self.values.reset()
        if EDEBUG:
            print('## Detailed Engine Info ## \n')
            print('IOEngine type: ', type(self))
            print()
            print('IOEngine Dir: ', dir(self))
            print()
            # print(self.engine_info())
            print()
            print('### Exiting IOEngine __init__ ### \n')
            print()

    def load_from_dict(self,
                         ioe_dict:dict,
                         iomapper=None,
                         evaluator=None):
        """Load  a new instance or reload an existing instance
           using same or new iomapper and evaluator."""

        for attr in self._export_attrs:
            if attr == 'mapper':
                setattr(self, 'mapper', iomapper or ioe_dict['mapper'] )
            elif attr == 'evaluator':
                setattr(self, 'evaluator', evaluator or ioe_dict['evaluator'])
            else:
                setattr(self, attr, ioe_dict[attr])

    def to_dict(self) -> dict:
        """Emit a dictionary of IOEngine basic defs and built internal
           structures.  Building the four xrefs and other internals
           causes visible ( 2 sec ! ) delay on a RP Rico.  Can speed
           up __init__ with from_dict parameter, used with IOMapper and
           Evaluator params for new instance."""

        ioe_dict = {}

        for attr in self._export_attrs:
            ioe_dict[attr] = getattr(self, attr)

        return ioe_dict

    def _expand_cmacros(self, cond_dict:dict[str,list[Condition]]) -> dict:
        """ dict[str,list[Condition|list[Condition]]]"""

        if EDEBUG and self.cond_macros:
            print('Expanding condition macros: ', self.cond_macros.keys())
            print()

        for k,v in cond_dict.items():

            new_conds = []
            for cond in v:

                if isinstance(cond, list ):
                    new_list = []
                    for c in cond:
                        if isinstance( c, CMacro ):
                            exp_conds = self.cond_macros[c.name]
                            new_list = [ex_cond for ex_cond in exp_conds]
                        else:
                            new_list.append(c)
                    new_conds.append(new_list)

                else:
                    if isinstance( cond, CMacro ):
                           exp_conds = self.cond_macros[cond.name]
                           for ex_cond in exp_conds:
                               new_conds.append(ex_cond)
                    else:
                        new_conds.append(cond)

            cond_dict[k] = new_conds

        return cond_dict


    def _build_cond_keys(self) -> list[tuple]:
        """List of occurances of value dict keys used in conditions,
           [( value_key1, condition1:int ),  slot position
            ( value_key1, condition2:int )]

          Used to build matches for values changed, re-eval action condition."""

        lhs_keys = [(cond.name_lhs,i) for i, cond in enumerate(self.condition_set)]
        rhs_keys = [(cond.name_rhs,i) for i, cond in enumerate(self.condition_set)
                      if isinstance(cond.name_rhs,str) and cond.name_rhs in self.values ]

        return list(chain(lhs_keys, rhs_keys))

    def _build_keys_used(self) -> int:
        """A mask for AND with values.changed int.
           Value keys used in conditions --> slot for vkeys in the values dict.
           ANDed with values_changed for 'changed and used' filter."""

        cond_keys = self._build_cond_keys()

        value_keys_used = set([ key for key, cond in cond_keys ])

        key_xref = 0
        for key in value_keys_used:
            key_xref |= 1 << self.values.vkeys.index(key)

        return key_xref


    def _build_cond_set(self) -> list[Condition]:
        """
          The Condition Set: a *list* of unique conditions that are used
          by perhaps several actions in the action:[Conditions] dict.
          Almost all xrefs map either to it or from it. Defines the 'key'
          to interpret evaluated conditions in cond_evals:int.

          self.cond_evals gets carried forward across binding cycles as
          something like a 'state vector'.

           [ Condition('age' , 'lt', 30),
             Condition('credit_rating', 'eq' 'Bad').
             Condition('credit_rating', 'eq' 'OK'),   # lhs and rhs from iom.values
             Condition('income', 'gte', 20000),       # rhs is python type
             Condition('income', 'lt', 20000),
            ... ]

           Action trigger 0b01101 would mean:
                Condition('age' , 'lt', 30) AND
                Condition('credit_rating', 'eq' 'OK') AND
                Condition('income', 'gte', 20000)

           An AND match between 0b01101 and the evaluated conditions
            ( ex. 0b01101 ) might  trigger the 'approve_loan' action in
            IOMapper.   The param 'applicant' in the values dict would
            provide a master ref to the attributes of the new customer."""

        conds = [cond for condlist in self.conditions.values() for cond in condlist]

        wcond_list:list = []  # working cond_list
        for cond in conds:
            if isinstance( cond, list):  # multiple OR triggers for action
                for con in cond:
                    wcond_list.append(con)
            else:
                wcond_list.append(cond)

        # Get rid of duplicated and sort

        return sorted(list(set([cond for cond in wcond_list])))

    def _build_action_trigger_xref(self) -> list[tuple]:
        """ Conditions <-- Action.  Main logic driver.

          Match trigger against eval conds, if match read/write action in iomapper.

            [('action_key1', 0b10101),   # OR
              'action_key1', 0b01010),
             ('action_key2', 0b01101) ]

          When match cond_evals ( 0b101110 & 0b01010 }, run 'action_key1', slot 1 trigger
         """

        at_xref = []

        for action, conds in self.conditions.items():
            if isinstance( conds[0], list): # multiple triggers, [[conds1] OR [conds2]]
                for cond in conds:
                    cond_trigger:int = 0
                    for con in cond:
                        i = self.condition_set.index(con)
                        cond_trigger |=  power2(i)
                    at_xref.append((action, cond_trigger))
            else:
                cond_trigger:int = 0
                for cond in conds:
                    i = self.condition_set.index(cond)
                    cond_trigger |=  power2(i)
                at_xref.append((action, cond_trigger))

        return at_xref

    def _build_cond_actions_xref(self) -> list[int]:
        """Condition --> Actions, map to action trigger xref
           Build list[int] containing xrefs to actions in action trigger xref
           Slot position is list is same as position in the cond_set.
           Used to build conflict set.

           cond_actions_xref:list[int] - """

        c_a_xref = [ 0 ] * len( self.condition_set)
        for i, act_trig in enumerate(self.action_trigger_xref):
            for index in bit_indexes(act_trig[1]):
                c_a_xref[index] |= power2(i)

        return c_a_xref

    def _build_key_conds_xref(self) -> dict[str,int]:
        """Value Key --> Conditions, where used map to cond_set.
           Similar to condition conflict sets. If key used in more than one condition,
           with different values in 'eq' relations, can not both be true."""

        cond_keys = self._build_cond_keys()

        kc_xref = { k: 0 for k, i in cond_keys}
        for k, i in cond_keys:
            kc_xref[k] |= power2(i)

        return kc_xref

    def _build_cond_keys_xref(self) -> list[int]:
        """ Condition slot --> Value Keys, map to values.vkeys.
            Should be two references unless rhs is Python type.
            Inverse of key_conds_xref.  Not used yet."""

        c_k_xref = [ 0 ] * len( self.condition_set)
        for k, v in self.key_conds_xref.items():
            for index in bit_indexes(v):
                c_k_xref[index] |= power2(self.values.vkeys.index(k))

        return c_k_xref

    # conflict_sets:list[set|str]
    def _build_conflict_sets(self) -> list[set]:
        """ conflict_sets: list[str|set]

            Conflicts between actions. Two types of conflict, conflicts
            between conditions and conflict bewteen actions.

            Conflicts between conditions are nearly impossible based
            on the unique source of values in the values dict. Maybe
            later in other usage scenaios.

            Action conflicts are any two acions that require a state
            change the same underlying object.  A conflict set may be either:

            1 - A set of names of actions in action_cond_xref that
            are in conflict.

            2 - A name of a value key in the values dict for a dependency
            chase -> conditions -> the action_triggers where used, returning
            a set of action names.

            If current state ( cond_evals ) AND condition conflict sets have
            more than one bit set, then conflict."""

        conflict_list:list[set] = []

        key_conds_xref: dict[str.int] = self._build_key_conds_xref()
        cond_actions_xref = self._build_cond_actions_xref()

        # action conflicts
        for conflict in self.conflict_sets:
            if isinstance(conflict, set):
                conflict_list.append(conflict)
            else:
                action_conflicts = { self.action_trigger_xref[aindex][0]
                    for cindex in bit_indexes(key_conds_xref[conflict])
                        for aindex in bit_indexes(cond_actions_xref[cindex])}

                conflict_list.append(set(action_conflicts))

        return conflict_list

        # potential condition conflicts, to find 'conflict key'
        # conflict_conditions:list[tuple] = [(cond, key) for key, cond in self.key_conds_xref.items()
        #                            if more_than_one_bit_set(cond)]
        # gets all, not just 'eq'


    ### Public Methods ###

    def evaluate_cond(self, cond:Condition):
        """Just evaluate a condition, no state change"""

        lhs, rel, rhs = cond
        vlhs = self.values[lhs]
        if isinstance(rhs, str) and rhs in self.values:
            vrhs = self.values[rhs]
        else:
            vrhs = rhs  # treated as python 'atomic'

        return self.evaluator.validate( rel, vlhs, vrhs )  # returns T or F


    def evaluate_all_conds(self):
        """Reset/synchronize local cond_evals to iomapper.values dict"""

        cond_evals = 0

        for i, cond in enumerate(self.condition_set):
            if self.evaluate_cond( cond ):
                cond_evals |= power2(i)

        self.cond_evals = cond_evals

    @property
    def agenda(self):

        return self.mapper.agenda

    def add_agenda(self, agenda):
        """Add command ( SetVal or Run ) for next cycle."""

        self.mapper.add_agenda(agenda)


    def run_cycle(self):
        """Run a binding cycle for iomapper.  This is the main entry
           point into IOEngine.  Must be implemented in subclass.
           """

        raise NotImplemented


    def run(self, limit:int=0):
        """Perform run_cycle 'limit' number of times"""

        n = 1

        while n <= limit:

            if EDEBUG: print('Running cycle: ', n)

            self.run_cycle()

            if EDEBUG:
                print('keys changed: ', self.values.keys_changed())
                print()

            n += 1



class TransactorEngine(IOEngineBase):
    """Transaction Type Event-Condition-Action Engine"""

    _export_attrs = ['mapper', 'evaluator', 'conditions', 'read_keys',
                     'cond_macros', 'conflict_sets', 'condition_set', 'key_conds_xref',
                     'action_trigger_xref' ]

    def __init__(self, *args, **kwargs):

        # print('TE init ', args, kwargs )
        # print('TE init ', args[0].values )

        super().__init__(*args, **kwargs )

        # action-to-cond(trigger) xref, built by default in IOEBase

        # key-to-condition xref,
        self.key_conds_xref: dict[str.int] = self._build_key_conds_xref()

        if EDEBUG:
            print('Engine Info')
            print(self.engine_info())
            print()

    def _find_changed_actions(self):
        return range(len(self.action_trigger_xref))


    def run_cycle(self):
        """Run a binding cycle for iomapper.  This is the main entry
           point into IOEngine.

           As set up, it runs in 'montitor mode' first and then in
           'transaction mode'."""

        self.mapper.read_into_values(self.read_keys)   # state changing

        if EDEBUG:
            print()
            print('Updated value dict: ', self.values)
            print()

        if EDEBUG:
            print('# Transactor Evaluation ( evaluate all )')

        # test engine type.  If 'monitor', else range(len(action_trigger_xref))

        changed_actions = self._find_changed_actions()

        if EDEBUG:
            print('Found changed actions -> ', changed_actions)
            print()

        actions = []

        changed_keys = list(set(self.values.keys_changed()).
                          intersection(set(self.key_conds_xref.keys())))

        if changed_keys:
            if EDEBUG: print('Changed keys ', changed_keys)

            self.evaluate_all_conds()

            if EDEBUG:
                print('Evaluated conditions: ', bin(self.cond_evals))
                print()

            for i, xref in enumerate(self.action_trigger_xref):
                if (xref[1] & self.cond_evals)==xref[1]:
                    if EDEBUG: print(f'Action {i} triggered: {xref[1]:>08b} -> {xref[0]}')
                    if xref[0] not in actions:
                        if EDEBUG: print(f"Action '{xref[0]}' added to actions list.")
                        actions.append(xref[0])
                    else:
                        if EDEBUG: print(f"Duplicate action '{xref[0]}' not added to actions list.")

        else:
            pass  # debugging

        if self.conflict_sets and actions:   # any actions to test

            actions_set = set(actions)
            for conflict_set in self.conflict_sets:
                if len(set(actions_set).intersection(conflict_set)) > 1:
                    raise IOEngineError(f'Conflicting actions in action list ', actions)

        for action in actions:
            if EDEBUG: print('Adding action to agenda: ', action, '\n')
            self.add_agenda(Run(action))


    def engine_info(self):

        einfo = []
        out = einfo.append

        out('IOEngine Info: External and Internal Structures')
        out('')

        out('Condition CMacro() expansions')
        out('cond_macros: ')
        for k, v in self.cond_macros.items():
            out(f"  {k}:     CMacro('{k}') -->:")
            for c in v:
                out(f'    {c}')
            out('')
        out('')

        out("Expanded conditions:   ( action: [Conditions] ) ")
        out('')
        for k, v in  self.conditions.items():
            out(f'  {k}:' )
            if isinstance(v[0], list):
                # out('v[0] is list', v[0])
                for conds in v:
                    # out('DEBUG ', conds)
                    for cond in conds:
                        out(f'  {cond}')
                    out('')
            else:
                # out('v[0] is not list', v[0])
                for cond in v:
                    out(f'  {cond}')
                out('')
        out('')

        out('condition_set:')
        for i, cond in enumerate(self.condition_set):
            out(f'  cond {i}  {cond}')
        out('')

        out('action_trigger_xref: ')
        for i, at_xref in enumerate(self.action_trigger_xref):
            out(f'  action {i}:  0b{at_xref[1]:>09b} -> {at_xref[0]}')
        out('')

        '''
        out('cond_actions_xref: (inverted action_trigger_xref)')
        for i, ref in enumerate(self.cond_actions_xref):
            out(f'  cond {i}   {ref:010b}')
        out('')
        '''

        '''
        out(f'Keys used, mapped to values dict {bin(self.keys_used)}')
        out('')
        '''

        out('key_conds_xref: value key used in conditions -> cond_set.')
        for key, cond in self.key_conds_xref.items():  # tuples
            out(f'  {key:16}  {cond:010b}')
        out('')

        out('conflict sets:')
        out(f'  {self.conflict_sets}')
        out('')

        return '\n'.join(einfo)


if __name__ == '__main__':

    from fan_mapper import  BasicFanIOMapper

    # EDEBUG = False
    EDEBUG = True
    iomapper.EDEBUG = True

    iom = BasicFanIOMapper()
    
 

    # Resolve references to underlying objects in IOMapper via values dict.
    # The way the example is set up, all values and constants come directly
    # from values dict.  Basic python types, int, str, float, boolean and
    # lists of basic types are all acceptable on the rhs.  Sets and tuples
    # are not directly jsonable.  See RuleSetLoader prepare/restore types.

    a_conditions = { 'fan_on' : [[Condition('fan_state', 'eq', 'fan_OFF' ),
                                Condition('room_temp', 'gt', 'upper_limit')],
                                # OR
                               [Condition('fan_state', 'eq', 'fan_OFF' ),
                                Condition('switch_state', 'eq', 'switch_ON')]],

                  'fan_off': [Condition('fan_state', 'eq', 'fan_ON' ),
                              Condition('switch_state', 'eq', 'switch_OFF'),
                              Condition('room_temp', 'lt', 'lower_limit')],
                  }

    conflicts = ['fan_state', {'switch_on', 'switch_off'}]

    # ioeng = IOEngineBase( iom, conditions=a_conditions, conflict_sets=conflicts )
    ioeng = TransactorEngine( iom, conditions=a_conditions, conflict_sets=conflicts )

    checkstats(ioeng.values)


    print('### Starting IOEngine Run ###')
    print()

    def erun(ioengn, limit):

        n = 1

        while n <= limit:

            print('### Running cycle: ', n)
            print()

            ioengn.run_cycle()

            if n==4:
                print('-> Injecting switch_on into agenda')
                ioeng.add_agenda(Run('switch_on'))
                print('agenda ', ioeng.agenda )
                print()

            if n==8:
                print('-> Injecting switch_off into agenda')
                ioeng.add_agenda(Run('switch_off'))
                print('agenda ', ioengn.agenda )
                print()

            print('agenda ', ioengn.agenda )
            print()

            n += 1

    erun(ioeng, 12)

    print()
    print('End ioeng.run.')
    print()

    checkstats(ioeng.values)

    print()
    print('=====   Test of Save/Load RuleSet   ===== \n')
    print('  * ioeng.to_dict -> rulesetloader prepare types and save to file')
    print('  * rulesetloader load file and restore types -> ioeng.load_from_dict')
    ioedict = ioeng.to_dict()
    print('Dict from ioeng.to_dict: \n')
    for k, v in ioedict.items():
        print(k, ':  ', v)
        print()

    loader = RuleSetLoader( iomappers= { 'BasicFanIOMapper': BasicFanIOMapper })
    loader.save(ioedict)
    print('--> Saved ioe_dict to json \n')
    print('--> deleting ioeng instance')

    del(ioeng)

    print('Testing load json  file from ioenginetest.json')
    if is_micropython():
        print()
        print('At this point, MicroPython will cause a JSON exception.  Maybe MRO ?')
        print("Sorry bout that - it's been a very persistent bug, still working on it.")
        print()

    EDEBUG = False

    print('loader create from_dict to build new IOEngine instance \n')
    from_dict = loader.load()

    print('Original dict == Restored dict ---> ', ioedict == from_dict)
    print()

    if ioedict != from_dict:
        print('Checking for diffs ')
        for k, v in ioedict.items():
            if v != from_dict[k]:
                print('key: ', k )
                print('orig:    ', v)
                print('restored:', from_dict[k])

    print()

    # print('IOEngine -> ioedict:')
    # print(ioedict)

    print('from_dict -> IOEngine')
    print(from_dict)
    print()

    print('Create new instance of IOEngine from restored json file \n' )
    ioeng2 = TransactorEngine(mapper=iom, from_dict=from_dict )
    print()
    print('ioeng2 engine_info')
    print(ioeng2.engine_info())

    EDEBUG = True

    print('Run engine 3 cycles \n')


    erun(ioeng2, 3)

    print('THE END')



