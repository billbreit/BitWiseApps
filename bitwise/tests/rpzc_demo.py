"""Simple Example of TableStore and DataStore for the ***Raspberry Pi Zero Club***

   Structure  Member.name -> Project.projleader
                           -> ProjectMember.member

              Resource.resource -> ProjectResource.resource

              Project.projname ->  ProjectResource.projname
                               ->  ProjectMember.projname

              Role.role        ->  ProjectMemeber.role

   """

try:
    from gc import mem_free, collect
    mem_free_present = True
    mem_start = mem_free()
    # from micropython import mem_info, qstr_info, stack_use
except:
    mem_free_present = False

"""
if mem_free_present:
    print('Starting memory, before imports, just gc and micropython funcs.')
    mem_info()
    qstr_info()
    stack_use()
"""

try:
    import fsinit
except:
    import tests.fsinit as fsinit
del(fsinit)

from tablestore import TableStore, TableDef, ColDef, display_table, TableStoreError
from tablestore import DataStore, DataStoreDef, RelationDef, ColDef, display_dbdef

"""User Types"""

from liststore import datetime, timestamp


class Members(TableStore):

    _tdef = TableDef(tname = 'Member',
                     filename = 'member',
                     unique=['name'],
                     col_defs = [ColDef(cname='name', default=None, ptype=str),
                             ColDef(cname='address', default='<unknown>', ptype=str),
                             ColDef(cname='phone', default='<unknown>', ptype=str),
                             ColDef(cname='email', default='<unknown>', ptype=str),
                             ColDef(cname='num_RPZeros', default=0, ptype=int),
                             ColDef(cname='date_joined', default=timestamp, ptype=datetime)])

    @property
    def members(self):

        return self.get_column('name')

    @property
    def oldest_member(self):
        """Need way to formalize"""


        row = min(iter(self), key = lambda x:x[self.slot_for_col('date_joined')])

        return row[self.slot_for_col('name')]

    @property
    def num_RPZs(self):

        return sum(self.get_column('num_RPZeros'))

    @property
    def inactive_members(self):

        pmems = set(self.db.ProjectMember.get_column('member'))

        return [ mem for mem in self.members if mem not in pmems ]


class Projects(TableStore):
    """Figure out how to rep benfactor = none"""

    _tdef = TableDef(tname = 'Project',
                     filename = 'project',
                     unique = ['projname'],
                     col_defs = [ColDef(cname='projname', default=None, ptype=str),
                                ColDef(cname='purpose', default='', ptype=str),
                                ColDef(cname='perks', default=[], ptype=list)])
    @property
    def projects(self):

        return self.get_column('projname')

class Roles(TableStore):
    """Role -> Role Behavior. Note seriously non-relational structure. """

    _tdef = TableDef(tname = 'Role',
                     filename = 'role',
                     unique = ['role'],
                     col_defs = [ColDef(cname='role', default=None, ptype=str),
                                 ColDef(cname='duties', default=[], ptype=list)])

    _default_roles = [['benefactor',['Membership in the Circle of Honor', 'newsletter',
                                       'free_lunch_program', 'key to executive restroom']],

                      ['projectleader',['central_contact', 'copy_recipient',
                                       'newsletter', 'chat_room_moderator',
                                       'free_lunch_program']],
                      ['workerbee',['newsletter', 'free_lunch_program',
                                    'chat_room_access']],
                      ['helper', ['newsletter','occasional_labor']]]

class ProjectMembers(TableStore):

    _tdef = TableDef(tname = 'ProjectMember',
                     filename = 'projectmember',
                     unique = ['projname', 'member'],
                     col_defs = [ColDef(cname='projname', default=None, ptype=str),
                                 ColDef(cname='member', default=None, ptype=str),
                                 ColDef(cname='projrole', default='helper', ptype=str)])

    def members(self, proj:str):

        return [ mem for projname, mem in zip(self.get_column('projname'),
                                          self.get_column('member'))
                                          if proj == projname ]

    @property
    def benefactors(self):

        return [ (m, p) for p, m, r in zip(self.get_column('projname'),
                                        self.get_column('member'),
                                        self.get_column('projrole'))
                                        if r == 'benefactor']

class Resources(TableStore):
    """Not sure what category is doing, like a rollup ?."""

    _tdef = TableDef(tname = 'Resource',
                     filename = 'resource',
                     unique = ['resource'],
                     col_defs = [ColDef(cname='resource', default=None, ptype=str),
                                 ColDef(cname='unit', default=None, ptype=str),
                                 ColDef(cname='category', default='<nocat>', ptype=str)])
    @property
    def resources(self):

        return self.get_column('resource')

class ProjectResources(TableStore):

    _tdef = TableDef(tname = 'ProjectResource',
                     filename = 'projectresource',
                     unique = ['projname', 'resource'],
                     col_defs = [ColDef(cname='projname', default=None, ptype=str),
                                ColDef(cname='resource', default=None, ptype=str),
                                ColDef(cname='amount', default=None, ptype=float),
                                ColDef(cname='note', default='', ptype=str)])

    def expenditure(self, resource:str=None ):
        """Aggregated expenditure for resource type"""

        if [resource] in self.db.Resource.keys():
            runit = self.db.Resource.get([resource], 'unit')
        else:
            raise TableStoreError(f"Resource '{resource}' not found")

        exp = sum([ amount for amount, res in zip(self.get_column('amount'),
                                       self.get_column('resource'))
                                       if res == resource ])
        return exp, runit

    def expense_report(self):

        resr = []
        for res in self.db.Resource.resources:
            exp, runit = self.expenditure(res)
            resr.append(f"{res:20} {exp:10} {runit}")

        return '\n'.join(resr)


class Events(TableStore):

    _tdef = TableDef(tname = 'Event',
                     filename = 'event',
                     unique = ['eventid'],
                     col_defs = [ColDef(cname='eventid', default=None, ptype=str),
                                ColDef(cname='title', default=None, ptype=str),
                                ColDef(cname='projname', default=None, ptype=str),
                                ColDef(cname='datetime', default=None, ptype=datetime),
                                ColDef(cname='duration', default=None, ptype=int)])

    def events_calendar(self):

        events = sorted(self.dump(), key= lambda x: x[self.slot_for_col('datetime')])
        evcal = [f'datetime               duration   event       title                         project']
        for ev in events:
            evcal.append(f"{str(ev.datetime):25}{ev.duration:<8} {ev.eventid:12}{ev.title:30}{ev.projname}")

        return '\n'.join(evcal)


class RPZeroClub(DataStore):
    """RP Zero Club Demo

        one -> many
        Member [projectleader]-> Project   [projname] -> ProjectResource
                                 Resource [resource] -> ProjectResource
        """

    _dbdef = DataStoreDef( dbname = 'RPZClub' , dirname = 'rpzclub',
            relations = [ RelationDef( 'Member', 'name', 'ProjectMember', 'member'),
                          RelationDef( 'Project', 'projname', 'ProjectMember', 'projname'),
                          RelationDef( 'Role', 'role', 'ProjectMember', 'projrole'),
                          RelationDef( 'Project', 'projname', 'ProjectResource', 'projname'),
                          RelationDef( 'Resource', 'resource', 'ProjectResource', 'resource'),
                          RelationDef( 'Project', 'projname', 'Event', 'projname')],

            table_defs = [Members, Projects, Roles, ProjectMembers, Resources, ProjectResources, Events])
            # table defs in load order, par -> child


if __name__=='__main__':

    if mem_free_present:
        collect()   # makes pcio/esp32 more consistent
        main_start = mem_free()

    nl = print

    nl()
    print('=== Demo for the Raspberry Pi Club ===')
    nl()
    print('Member subclass of TableStore, without DataStore')
    nl()

    mems = Members()  # table class name

    data = [["Bill", "22 AnyWhere", "999-888-7777", "billb@xxx.net", 17, (2023, 6, 6, 9, 49, 57) ],
        ["Bob K.", "44 AnyWhere But Here", "222-333-4447", "bobk@yyy.net", 4],
        ["Sally", "22 AnyWhere", "999-888-7777", "sally@xxx.net", 0, (2023, 6, 6, 9, 49, 57) ],
        ["Sam", "66 EveryWhere", "888-444-44447", "samy@yyy.net", 1],
        ["Mary", "88 NoWhere", "888-444-0000", "mary@zzz.net", 18]]

    mems.extend(data)

    display_table(mems)
    nl()
    
    print('Members:       ', mems.members)
    print('Num RPZs:      ', mems.num_RPZs)
    print('Oldest member:  ', mems.oldest_member)
    nl()

    print('Member Table Definition')
    nl()
    print(Members._tdef)
    nl()
    print('Deleting Member Table, creating RPZeroClub DB')
    nl()

    del(mems)
    del(data)

    try:    print(mems, data)
    except: print('mems and data gone ')
    nl()

    rpzdb = RPZeroClub()
    print("dir(rpzdb) instance", dir(rpzdb))
    nl()

    dbdef = rpzdb.dbdef

    display_dbdef(dbdef)
    nl()


    memdata = [["Bill", "22 AnyWhere", "999-888-7777", "billb@xxx.net", 17, (2023, 6, 6, 9, 49, 57) ],
        ["Bob K.", "44 AnyWhere But Here", "222-333-4447", "bobk@yyy.net", 4, (2023, 7, 7, 0, 0, 0)],
        ["Sally", "22 AnyWhere", "999-888-7777", "sally@xxx.net", 0, (2023, 6, 6, 9, 49, 58) ],
        ["Sam", "66 EveryWhere", "888-444-44447", "samy@yyy.net", 1],
        ["Mary", "88 NoWhere", "888-444-0000", "mary@zzz.net", 18],
        ['Building The Future Corp.', '777 Dynomo Cresent'],
        ['PaleoAmericans4Progress.org', '333 Happy Acres Rest Home']]

    mems = rpzdb.Member  # db.attr table name versus Members class name

    mems.extend(memdata)

    display_table(mems)
    nl()

    print('Members:       ', mems.members)
    print('Num RPZs:      ', mems.num_RPZs)
    print('Oldest member: ', mems.oldest_member)
    nl()

    projdata = [['Build New Tools', 'Build some dev tools', ['free lunch program']],
                ['Clean Up Lab Area',  'Vacuuming, dusting'],
                ['Educating The Inept', 'Basic skills for those with none', ['free lunch program']]
                ]

    projs = rpzdb.Project

    projs.extend(projdata)

    display_table(projs)
    nl()
    print( 'Project val row ', projs.validate_row(['Clean Up Labs Areaxx', 'Vacuuming, dusting']))
    nl()

    ###################### Role ##################


    roledata = [['benefactor',['Lifetime Membership in the Circle of Honor', 'newsletter',
                                       'free_lunch_program', 'key to executive restroom']],
                ['projectleader',['central_contact', 'copy_recipient', 'newsletter',
                                  'chat_room_moderator', 'free_lunch_program']],
               ['workerbee',['newsletter', 'free_lunch_program',
                             'chat_room_access']],
               ['helper', ['newsletter','occasional_labor']]]

    roles = rpzdb.Role

    roles.extend(roledata)

    display_table(roles)
    nl()

    print('getcol role ', roles.get_column('role'))
    print('getcol duties ', roles.get_column('duties'))
    print('col names ', roles.column_names)
    print('slot role ', roles.slot_for_col('role'))
    print('slot duties', roles.slot_for_col('duties'))
    nl()

    projmemdata = [['Build New Tools', 'Bill', 'projectleader'],
                   ['Build New Tools', 'Bob K.', 'workerbee'],
                   ['Build New Tools', 'Mary', 'helper'],
                   ['Build New Tools', 'Building The Future Corp.', 'benefactor'],
                   ['Clean Up Lab Area', 'Bill', 'helper'],
                   ['Clean Up Lab Area', 'Sally', 'projectleader'],
                   ['Educating The Inept', 'Mary', 'projectleader'],
                   ['Educating The Inept', 'PaleoAmericans4Progress.org', 'benefactor']]

    projmems = rpzdb.ProjectMember

    projmems.extend(projmemdata)

    display_table(projmems)
    nl()
    
    print('Invalid row     : ', projmems.validate_row(['Clean Up Labs Areaxxx', 'Sam']))
    print('Inactive members: ', mems.inactive_members)
    print("Project members for 'Clean Up Lab Area' ", projmems.members("Clean Up Lab Area"))
    print("Valide row ['Educating The Inept', 'Mary'] ",
             projmems.validate_row(['Educating The Inept', 'Mary']))
    print("Validate parent for ['Educating The Unwary', 'Mary', 'unhelpful'] ",
             projmems.validate_parents(['Educating The Unwary', 'Mary', 'unhelpful']))
    print('Project Benefactors ', projmems.benefactors)
    nl()

    rdata = [['time', 'hours', 'volunteer time'],
             ['parts', 'dollars', 'money' ],
             ['materials', 'dollars', 'money' ],
             ['food', 'dollars', 'money' ],
             ['sundry', 'dollars', 'money' ],
             ['loaned rpz', 'units', 'devices'],
             ['owned rpz', 'units', 'devices']]

    res = rpzdb.Resource

    res.extend(rdata)

    res.append(['miscellaneous', 'dollars' ])

    display_table(res)
    nl()

    projr = rpzdb.ProjectResource

    prdata = [['Build New Tools', 'time', 100],
              ['Build New Tools', 'parts', 102, '6 RP Picos w/headers !'],
              ['Build New Tools', 'materials', 152.01],
              ['Build New Tools', 'food', 404.03],
              ['Build New Tools', 'loaned rpz', 5],
              ['Clean Up Lab Area', 'time', 2.4 ],
              ['Clean Up Lab Area', 'materials', 3.97],
              ['Clean Up Lab Area', 'sundry', 103.99],
              ['Clean Up Lab Area', 'miscellaneous', 11.44],
              ['Educating The Inept', 'miscellaneous', 22.17, 'snacks']]

    projr.extend(prdata)

    display_table(projr)
    nl()

    print('Expenses for project resource xxx')
    try:
        print('expenses for xxx', projr.expenditure('xxx'))
    except Exception as exc:
        print(exc)
    nl()

    evt = rpzdb.Event


    evdata = [['BNT 101', 'New Tools Tutorial Part 1','Build New Tools', (2024, 6, 9, 16, 0, 0), 60],
              ['BNT 102', 'New Tools Tutorial Part 2','Build New Tools', (2024, 6, 16, 16, 0, 0), 60],
              ['Org111', 'Planning Summit Session', 'Clean Up Lab Area', (2024, 6, 12, 12, 0, 0), 180],
              ['Org112', 'Advanced Planning', 'Clean Up Lab Area', (2024, 6, 14, 12, 0, 0), 180],
              ['SFTE0', 'Soldering For The Elderly', 'Educating The Inept', (2024, 7, 14, 8, 0, 0), 480]]

    evt.extend(evdata)

    display_table(evt)
    nl()

    nl()
    print('rpzcdb.tables_changed() ', rpzdb.tables_changed())
    print('reset_all')
    rpzdb.reset_all()
    print('rpzcdb.tables_changed() ', rpzdb.tables_changed())
    mems.append(['Tommy', '222 Old Same Place','444-666-888','tt@xxx.net', 3])
    print("Added New Member 'Tommy', tables_changed() -> ", rpzdb.tables_changed())
    ctab = rpzdb.table(rpzdb.tables_changed()[0])
    print(ctab.get_rows(ctab.rows_changed()))
    print('Num RPZs:          ', ctab.num_RPZs)
    print('Inactive members: ', ctab.inactive_members)
    nl()

    print('Upcoming Events: ')
    print('-' * 80)
    print( evt.events_calendar())
    nl()

    # some sort of form ?
    nl()
    print('Expense Report: ')
    print('-' * 40)
    print(projr.expense_report())

    nl()
    print('Saving DB ...')
    rpzdb.save_all()

    print('Reloading DB ...')
    rpzdb2 = RPZeroClub()
    rpzdb2.load_all()
    print()


    # print('locals()')
    # print(locals())

    """
    print(f"===   DB Display for Recovered {rpzdb2.dbname}   ===")
    nl()
    for n, tb in rpzdb2.tables():
        display_table(tb)
    """

    import sys

    if mem_free_present:

        main_end = mem_free()
        print(f"=== Memory Usage for MicroPython on {sys.platform} ===")
        print()
        print('High level executive summary - gc is very mysterious.')
        
        """
        print('mem_info ')
        mem_info()
        print('qstr_info ')
        qstr_info()
        print('stack_use ')
        stack_use()
        """
        
        print('Total memory started: ', mem_start )
        print('Memory use to start of __main___ collected :', mem_start-main_start)
        print('Mem free at end: ', mem_free())
        print('Total memory used: ', mem_start-main_end)
        nl()
        collect()
        print('Mem free after collect: ', mem_free())
        print('Mem used after collect: ',  mem_start-mem_free())
        nl()
        del rpzdb2
        collect()
        print('Mem free after del restored db and collect: ', mem_free())
        print('Mem used after del restored db and collect: ',  mem_start-mem_free())
        nl()

        del dbdef
        del memdata
        del projdata
        del roledata
        del projmemdata
        del rdata
        del prdata
        del evdata


        del mems   # no effect on mem_free
        del projs
        del roles
        del projmems
        del res
        del projr
        del evt
        del ctab

        collect()
        print('Mem free after del source data/refs and collect: ', mem_free())
        print('Mem used after del source data/refs and collect: ',  mem_start-mem_free())
        print('... Pico locals() says delled, dangling references ?')
        nl()
        del rpzdb
        collect()
        print('Mem free after del original db and collect: ', mem_free())
        print('Mem used after del original db and collect: ',  mem_start-mem_free())
        print('Using loop del reduces memory, but doesn\'t remove from locals.')
        print('Using inline del removes from locals, but doesn\'t reduce memory.')
        print('before ... qstring ? maybe scanning usage and anticipating ?')
        print('after ... now it\'s reducing memory (???).')
        print('Missing 4K that can\'t account for ? qstr most likely.  Or base heap realloc ?  ')
        nl()
        # print('locals ', locals())  # mpy, use line command
        # print(memdata)

    else: # Python

        from gc import get_stats
        from sys import getsizeof   # almost useless

        print()
        print('Python Stats Start' )
        print(get_stats())
        print('get size of rpzdb ', getsizeof(rpzdb))
        print('get size of rpzdb2 ', getsizeof(rpzdb2))
        print('get size of memdata ', getsizeof(memdata))
        print('get size of mems ', getsizeof(mems.store))
        print('get size of projmems ', getsizeof(projmems.store))


        tt = ['hello yall' + str(i) + 'testing' for i in range(200)]
        print('get size of tt ', getsizeof(tt))


        del(rpzdb)
        del(rpzdb2)
        # for d in [memdata, projdata, roledata, projmemdata, rdata, prdata, evdata]:
        #    print('about to del ', d)
        #    del(d)

        del dbdef
        del memdata
        del projdata
        del roledata
        del projmemdata
        del rdata
        del prdata
        del evdata

        del mems   # no effect on mem_free
        del projs
        del roles
        del projmems
        del res
        del projr
        del evt
        del ctab
        print()
        print('Python Stats End' )
        print(get_stats())
        print()

        # print('locals() ')
        # print( locals())

    # still working ?
    # rpzdb = RPZeroClub()
    # print(rpzdb)

































