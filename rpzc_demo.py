"""Simple Example of TableStore and DataStore for the ***Raspberry Pi Zero Club*** """ 


from tablestore import TableStore, TableDef, ColDef, display_table, DBDef_fields, TableStoreError 
from tablestore import DataStore, DataStoreDef, RelationDef, ColDef

class Members(TableStore):

    _tdef = TableDef(tname = 'Members',
                     filename = 'members',
                     unique=['name'],
                     col_defs = [ColDef(cname='name', default=None, ptype=str),
                             ColDef(cname='address', default='<unknown>', ptype=str),
                             ColDef(cname='phone', default='<unknown>', ptype=str),
                             ColDef(cname='email', default='<unknown>', ptype=str),
                             ColDef(cname='num_RPZeros', default=0, ptype=int)])
                             
    @property
    def members(self):
    
        return self.get_column('name')
    
    @property   
    def num_RPZs(self):
    
        return sum(self.get_column('num_RPZeros'))
        
class Projects(TableStore):

    _tdef = TableDef(tname = 'Projects',
                     filename = 'projects',
                     unique = ['projname'],
                     col_defs = [ColDef(cname='projname', default=None, ptype=str),
                                ColDef(cname='projleader', default=None, ptype=str),
                                ColDef(cname='purpose', default=None, ptype=str)])
                             
    @property
    def projects(self):
    
        return self.get_column('projname')
        
class Resources(TableStore):

    _tdef = TableDef(tname = 'Resources',
                     filename = 'resources',
                     unique = ['resource'],
                     col_defs = [ColDef(cname='resource', default=None, ptype=str),
                                 ColDef(cname='unit', default=None, ptype=str),
                                 ColDef(cname='category', default='<nocat>', ptype=str)])
        
class ProjectResources(TableStore):

    _tdef = TableDef(tname = 'ProjectResources',
                     filename = 'projectresources',
                     unique = ['projname', 'resource'],
                     col_defs = [ColDef(cname='projname', default=None, ptype=str),
                                ColDef(cname='resource', default=None, ptype=str),
                                ColDef(cname='amount', default=None, ptype=float)])
                                
    def expenditures(self, resource=None ):
    
        rt = self.db.table('Resources')
      
        if [resource] in rt.keys():
            runit = rt.get([resource], 'unit')
        else:
            raise TableStoreError(f"Resource '{resource}' not found")  
       
        exp = sum([ amount for amount, res in zip(self.get_column('amount'),
                                       self.get_column('resource'))
                                       if res == resource ])
        
        return exp, runit   
        
                            

class RPZeroClub(DataStore):

        _dbdef = DataStoreDef( dbname = 'RPZClub' , dirname = 'rpzclub',
                relations = [ RelationDef( 'Members', 'name', 'Projects', 'projleader'),
                              RelationDef( 'Projects', 'projname', 'ProjectResources', 'projname'),               
                              RelationDef( 'Resources', 'resource', 'ProjectResources', 'resource')],
                           
                table_defs = [Members, Projects, Resources, ProjectResources])
                # table defs in load order, par -> child 

def display_dbdef(dbdef):

    print('===   DB Definition   ===')
    print('DB name:    ', dbdef.dbname)
    print('DB dirname: ', dbdef.dirname)
    print()
    print(dbdef.relations)
    print()
    for i in range(len(dbdef.table_defs)):
        print( dbdef.table_defs[i])
        print()

                
if __name__=='__main__':

    """
    print()
    print('Relations')
    print('tabledict ', rpzdb.tabledict)
    print('tables() ', rpzdb.tables())
    for n, t in rpzdb.tables():
        print( n, t.tablename, t._prelations, t._crelations )
    """
    
    print('=== Demo for the Raspberry Pi Club ===')
    print()
    print('Members subclass of TableStore, without DataStore')
    print()

    mems = Members()
    
    data = [["Bill", "22 AnyWhere", "999-888-7777", "billb@xxx.net", 17],
        ["Bob K.", "44 AnyWhere But Here", "222-333-4447", "bobk@yyy.net", 4],
        ["Sally", "22 AnyWhere", "999-888-7777", "sally@xxx.net", 0],
        ["Sam", "66 EveryWhere", "888-444-44447", "samy@yyy.net", 1],
        ["Mary", "88 NoWhere", "888-444-0000", "mary@zzz.net", 18]]
        
     
    mems.extend(data)
     
    display_table(mems)
    
    print()
    print('Members ', mems.members)
    print('Num RPZs ', mems.num_RPZs)
    print()
    
    print('Members Table Definition')
    print()
    print(Members._tdef)
    print()
    print('Deleting Members Table, creating RPZeroClub DB')
    print()
    
    del(mems)
    
    rpzdb = RPZeroClub()
    
   
    dbdef = rpzdb.dbdef
    
        
    display_dbdef(dbdef)
    print() 
    
    
    memdata = [["Bill", "22 AnyWhere", "999-888-7777", "billb@xxx.net", 17],
        ["Bob K.", "44 AnyWhere But Here", "222-333-4447", "bobk@yyy.net", 4],
        ["Sally", "22 AnyWhere", "999-888-7777", "sally@xxx.net", 0],
        ["Sam", "66 EveryWhere", "888-444-44447", "samy@yyy.net", 1],
        ["Mary", "88 NoWhere", "888-444-0000", "mary@zzz.net", 18]]
     
        
    mems = rpzdb.table('Members')
    
 
    mems.extend(memdata)
    
    display_table(mems)
    print()
    
    projdata = [['Build New Tools', 'Bill', 'Build some dev tools'],  
                ['Clean Up Lab Area', 'Sally', 'Vacuuming, dusting']]    
    
    
    projs = rpzdb.table('Projects')
    
    print( 'val row ', projs.validate_row(['Clean Up Labs Area', 'xxxSally', 'Vacuuming, dusting'])) 
    print()
    projs.extend(projdata)

    display_table(projs)
    print()
    
    rdata = [['time', 'hours', 'volunteer time'],
             ['parts', 'dollars', 'money' ],
             ['materials', 'dollars', 'money' ],
             ['sundry', 'dollars', 'money' ],
             ['loaned rpz', 'units', 'devices'],
             ['owned rpz', 'units', 'devices']]
             
    res = rpzdb.table('Resources')
    
    res.extend(rdata)
    
    display_table(res)
    print()
    
    projr = rpzdb.table('ProjectResources')
    
    prdata = [['Build New Tools', 'time', 100],
              ['Build New Tools', 'parts', 100],
              ['Build New Tools', 'materials', 100],
              ['Build New Tools', 'loaned rpz', 5],
              ['Clean Up Lab Area', 'time', 2.4 ],
              ['Clean Up Lab Area', 'materials', 3.99],
              ['Clean Up Lab Area', 'sundry', 113.99]]
              
    projr.extend(prdata)
    
    display_table(projr)
    print() 
    
    # for r in res.keys():
    #    print(f"Expense {r}: {projr.expenses(r)}") 
    print('Expenditures: ')
    print('time          ', projr.expenditures('time'))
    print('materials     ', projr.expenditures('materials'))
    print('sundry        ', projr.expenditures('sundry'))
    print('owned rpz     ', projr.expenditures('owned rpz'))
    print('loaned rpz    ', projr.expenditures('loaned rpz'))

    try: print('expenses for xxx', projr.expenditures('xxx'))
    except Exception as exc: print(exc)
        
    

    print()
    
    print('Saving DB ...')
    rpzdb.save_all()
    
    rpzdb2 = RPZeroClub()
    rpzdb2.load_all()
    
    """
    print(f"===   DB Display for Recovered {rpzdb2.dbname}   ===") 
    print()
    for n, tb in rpzdb2.tables():
        display_table(tb)
    """
    
    
    
    
         
              
    


    
    
    
    
    
    

   
     
     
        
    
    

    
