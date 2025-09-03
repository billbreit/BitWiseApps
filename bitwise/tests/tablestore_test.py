
try:
    from gc import mem_free, collect
    mem_free_present = True
    mem_start = mem_free()
except:
    mem_free_present = False
    
from collections import namedtuple 
import json   

try:
    import fsinit
except:
    import tests.fsinit as fsinit
del(fsinit)

import sys, os
print('os.cwd ', os.getcwd())
print('sys.path ', sys.path)

### Something happened here.  fsinit was working and then it wasn't

try:
    from lib.tuplestore  import TupleStore    
    from lib.tablestore import TableStore, TableDef, TDef_fields, DataStore, DataStoreDef
    from lib.tablestore import ColDef, RelationDef, DBTableDef, timestamp, datetime, display_table
    from lib.tablestore import DBDef_fields
except:
    from tuplestore  import TupleStore    
    from tablestore import TableStore, TableDef, TDef_fields, DataStore, DataStoreDef
    from tablestore import ColDef, RelationDef, DBTableDef, timestamp, datetime, display_table
    from tablestore import DBDef_fields

if __name__ == '__main__':

    nl = print

    
    nl()
    print('=== Test of TableStore/DataStore Classes ===')
    nl()
    
    if mem_free_present:
        collect()   # makes pico/esp32 more consistent
        main_start = mem_free()
        
    # adds about 2-3k to base memory,
    # also seems to force collect of import alloc  ?
    try:
        from lib.indexer import Indexer
    except:
        from indexer import Indexer        

    
    # User Type
    
    MyTuple = namedtuple('MyTuple', [ 'x', 'y', 'z'])
    # DateTime = namedtuple('DateTime', [ 'year', 'month', 'day', 'hour', 'min', 'secs' ])  # no millis or micros in myp ?
    
    tdef = TableDef(tname = 'Test', filename = 'testing111', unique=['col1','col2'],
                     col_defs = [ColDef(cname='col1', default=None, ptype=str),
                                 ColDef(cname='col2', default=0, ptype=int),
                                 ColDef(cname='col3', default=0.0, ptype=float),
                                 ColDef(cname='col4', default={}, ptype=dict),
                                 ColDef(cname='col5', default=[], ptype=list),
                                 ColDef(cname='col6', default=(0, 0, 0), ptype=tuple),
                                 ColDef(cname='col7', default=(0, 0, 0), ptype=MyTuple),
                                 ColDef(cname='col8', default=False, ptype=bool),
                                 ColDef(cname='col9', default=timestamp, ptype=datetime),
                                 ]
                    )
    
    print('== TableDef ==')
    nl()
    for n, l in zip(TDef_fields, tdef):
        print(n, ': ', l)
    nl()
    
    tstore = TableStore(tdef )
    
    print('dir(tstore) ', dir(tstore))
    nl()
    
    print('Extend tstore with errors ')
    nl()
    
    try:
        tstore.extend([['a', 3, 1.1],
                    ['d', 'e', 'f'],
                    ['g', 'h', 'i']])
    except Exception as e:
        print(e)
        nl()

    tstore.extend([['a', 2, 1, {'d': 'testing'}, ['aaa', 'bbb', 'ccc' ], ( 4, 4, 4 ), ( 7, 8, 9 ), True ],
                    ['d', 4, 2.2],
                    ['g', -2],
                    ['kk', 77]])
                    
    print('Extend tstore with no errors ')
    nl()
                    
    for t in iter(tstore):
        print(t)
    nl()
    
    print('reset_changed()')
    tstore.reset_changed()
    nl()
        
    print("set(['a', 2 ], 'col3', 77.77) ")
    tstore.set(['a', 2 ], 'col3', 77.77)
    print("set(['kk', 77], 'col7', ( 12, 11, 10 )")
    tstore.set(['kk', 77], 'col7', ( 12, 11, 10 ))
    nl()
    print('Columns changed ', [bin(i) for i in tstore.changed])
    print('Rows changed    ', bin(tstore.rows_changed()))
    nl()
    
    print("tstore.fetch_key(['kk', 77]")
    print(tstore.fetch_key(['kk', 77]))
    nl()
    
    print('Columns changed ', [bin(i) for i in tstore.changed])
    print('Rows changed    ', bin(tstore.rows_changed()))
    nl()
    
    print("Appending ['LLL', 230 ] ...")
    tstore.append(['LLL', 230, 22, {'aaa':None, 'BBB':123}, ['List of stuff', 'More stuff' ], ( 3, 4, 5 ), (1, 1, 1 ), True])
    print("Appending ['LLL', 230 ] ... again. ")
    try:
        tstore.append(['LLL', 230, 22, {'aaa':None, 'BBB':123}, [333], ( 3, 4, 5 )])  # -> error
        print('Appending ERROR ... Should have been error for is_duplicate: ')
    except Exception as e:
        print('Appending ... is_duplicate: ', e )
    nl()
    print("Appending ['MMM', 6 ] and ['MMM', 3 ]")
    tstore.append(['MMM', 6 ])
    tstore.append(['MMM', 3 ])
    nl()
    
    print("Indexing 'col1' (str) and 'col7' (tuple)") 
    tstore.index_attr('col1')
    tstore.index_attr('col7')

    nl()
    print('=== Display TStore ===')
    nl()
    display_table(tstore)
    nl()
    
    for t in iter(tstore):
        print(t)
    nl()
    
    print('tstore.keys()')
    for k in tstore.keys():
        print(k)
    nl()
    
    print("is_duplicate(['MMM', 0] ", tstore.is_duplicate(['MMM', 0]))
    print("is_duplicate(['MMM', 3] ", tstore.is_duplicate(['MMM', 3]))
    
    print("is_duplicate(['NNN'] -> Error ")
    try:
        tstore.is_duplicate(['NNN'])
    except Exception as e:
        print('Bad Key Error: ' , e )
    nl()
    
    
    
    print("find_unique(['a', 0] ", tstore.find_unique(['a', 0]))
    print("find_unique(['LLa', 230] ", tstore.find_unique(['LLa', 230]))
    print("find_unique(['d', 4] ", tstore.find_unique(['d', 4]))
    nl()
        
    tstore.set(['d', 4 ], 'col2', 999 )
    tstore.set(['g', -2 ], 'col4', {'a':0})
    
    print('Columns changed ', [bin(i) for i in tstore.changed])
    print('Rows changed    ', bin(tstore.rows_changed()))
    nl()
    print("tstore.fetch_key(['g', -2 ]")
    print(tstore.fetch_key(['g', -2 ]))
    print("tstore.fetch_key(['MMM', 3 ]")
    print(tstore.fetch_key(['MMM', 3 ]))
    nl()
    print('Columns changed ', [bin(i) for i in tstore.changed])
    print('Rows changed    ', bin(tstore.rows_changed()))
    nl()

    sl = tstore.find_unique(['d', 999])
    print("Get_key row ['d', 999]" )
    print(tstore.get_key(['d', 999]))
    print("Get key  row ['d', 999], asdict=True")
    print(tstore.get_key(['d', 999], asdict=True))
    nl()
    print("Get row {'g', -2]", tstore.get_key(['g', -2]))
    nl()
    
    try:
        tstore.check_slot(33)
    except Exception as e:
        print('Bad slot test: ', e )
    print('TableStore len: ', tstore.length)
    nl()
    
    print('Dump ')
    for r in tstore.dump():
        print(r)
    nl()
        
    print('Saving ...')
    tstore.save()
    print('Saved')
    nl()
    fname = tstore.filename
    # del(tstore)

    fname = fname + ".json"

    with open( fname, "r") as file:
        data = json.load(file)
        
    print('Saved JSON file')
    for l in data: print(l)
    nl()
    
    print('Loading ...')
    tstore2 = TableStore(tdef)
    tstore2.load()
    print('Loaded ...  table.store with restored tuple types  ')
    print(tstore2.store)
    nl()
    print('Dump ')
    for r in tstore2.dump():
        print(r)
    nl()
    print('Dump - resolve types ( col7 tuple -> MyTuple, col9 -> datetime )')
    for r in tstore2.dump(resolve_types=True):
        print(r)
    nl()
    
    # print(tstore2.find_unique(['a', 'c']))
    
    keys = tstore2.keys()
    print('keys ', keys )
    nl()
    
    """
    print('extend new !!!')
    p1 = [  [ 'd', 'test d '],
            [ 'e', 'test e '],  
            [ 'f', 111100000000]]
    """
                    
    vl = [1.1, 2, 'hello', ( 1, 2, 3 ), [ 'a', 'b', 'c' ], {'one':1}, True]
    
    print('Value to test: ', vl )
    nl()
    print("Check types for list of values against 'col3' (float) ", tstore2.check_column_types('col3', vl))
    nl()
    print("Check types for list of values against 'col5' (list) ", tstore2.check_column_types('col5', vl))
    nl()
    print("Note that 'hello' and {'one':1} pass as lists ( int 1 gets lost ). May need strict types, isinstance ?")
    nl()
    print("get_column('col3') ", tstore2.get_column('col3'))
    print("sum(get_column('col3')) ", sum(tstore2.get_column('col3')))
    nl()
    try:
        x = tstore2.get_column('xxx') 
    except Exception as e:
        print('Bad col name for get_column: ', e ) 
    
    # display_table(par2t)
    nl()
    
    nl()
    print('=====  DataStore  =====')
    nl()
    print('dir(DataStore) ', dir(DataStore))
    nl()
    

    dbdef = DataStoreDef(
                dbname = 'Test' , dirname = 'testdata',
                relations = [ RelationDef( 'partable1', 'col1', 'chtable', 'col1'),
                              RelationDef( 'partable2', 'col1', 'chtable', 'col2')],
                           
                table_defs = [ DBTableDef( 'partable1',
                                    filename = 'partable1', ttype=TableStore, unique = ['col1'],
                                    col_defs = [ColDef(cname='col1', default='', ptype=str),
                                                ColDef(cname='col2', default='', ptype=str)]),
                                                             
                                DBTableDef( 'partable2',
                                     filename = 'partable2', ttype=TableStore, unique = ['col1'],
                                     col_defs = [ColDef(cname='col1', default='', ptype=str),
                                                 ColDef(cname='col2', default='', ptype=str)]),
                                                             
                                DBTableDef( 'chtable',
                                     filename = 'chtable', ttype=TableStore, unique = ['col1','col2'],
                                     col_defs = [ColDef(cname='col1', default='', ptype=str),
                                                 ColDef(cname='col2', default='', ptype=str),
                                                 ColDef(cname='col3', default='', ptype=str)])])                                                                            
                                                             
    for n, l in zip( DBDef_fields, dbdef):
        if isinstance(l, list):
            print(f'{n}: ')
            for ll in l:
                print(f'{ll}')
            nl()
        else:
            print(f'{n}: {l}')
    
    nl()

    tdb = DataStore(dbdef)
    print('dir(DataStore) instance ', dir(tdb))
    nl()
    for n, t in tdb.tables():
        print('table    ', n )
        print('instance ', t )
        print('parent of', t._prelations)
        print('child of ', t._crelations)
        nl()
        
    p1 = [  [ 'a', 'test a '],
            [ 'b', 'test b '],  
            [ 'c', 'test c ']]
                    
    tdb.table('partable1').extend(p1)
    
    p2 = [  [ 'x', 'test x '],
            [ 'y', 'test y '],  
            [ 'z', 'test z ']]  
            
    tdb.table('partable2').extend(p2)
            
    ch = [[ 'a', 'x', 'testing a.x'],
         [ 'a', 'z', 'testing a.z'],
         [ 'b', 'y', 'testing b.y'],
         [ 'b', 'z', 'testing2 b.y'],
         [ 'c', 'z', 'testing c.z']]    

    tdb.table('chtable').extend(ch)
    nl()
    
    for tname, tbl in tdb.tables():
        display_table(tbl)
    nl()
    
    print('Reset changed masks for all tables in DB, tdb.reset_all()')
    tdb.reset_all()
    print('Changed masks ', [(n , t.changed) for n, t in tdb.tables()])
    nl()
    
    cht = tdb.table('chtable')
    cht.reset_changed()
    
    print('Reset first, then set some values ')
    print("set([ 'a', 'x'], 'col3', 'testing a.x again !')")
    cht.set([ 'a', 'x'], 'col3', 'testing a.x again !') 
    print('new row: ', cht.get_key(['a','x']))
    nl()
    print("set([ 'a', 'x'], 'col2', 'y): change key.")
    cht.set([ 'a', 'x'], 'col2', 'y')
    print('new row: ', cht.get_key(['a','y']))
    nl()    
    print("set([ 'a', 'y'], 'col2', 'z): change key -> duplicate key error.")   
    try:
        cht.set([ 'a', 'y'], 'col2', 'z')
    except Exception as e:
        print('Set column to duplicate key error: ', e)
    nl()
    print("set([ 'a', 'y'], 'col2', 'mmm'): change key -> no parent error.")    
    try:
        cht.set([ 'a', 'y'], 'col2', 'mmm')
    except Exception as e:
        print('Set column no parent error: ', e)
    nl()
    print('Columns changed ', [bin(i) for i in cht.changed] )
    print('Rows changed   ', bin(cht.rows_changed()) )
    nl()       
    
    
    print('DB save, using tdb.save_all')
    tdb.save_all()
    nl()
    tdb2 = DataStore(dbdef)
    print('Create new DB and load, tdb.load_all')
    tdb2.load_all()
    nl()
    
    print('Examining parent and child tables ... using attrs.')
    nl()
    par2t = tdb2.partable2
    cht = tdb2.chtable
    print( 'DBUG ', par2t, cht )
    print("parent table: parents_exist ['a', 'mmm']       ", par2t.parents_exist([ 'a', 'mmm']), ' -> problem, has no parents, so has required parents is True')
    print("parent table: children_exist ['x', 'mmm']      ", par2t.children_exist([ 'x', 'mmm']))
    print("parent table: val children ['y', 'mmm']        ", par2t.validate_children([ 'y', 'mmm']))
    print("child table: val parents ['m','n']             ", cht.validate_parents([ 'm', 'n', 'testing a.z']))
    print("child table: validate row [ 'a', 'z', (1,2,3)] ", cht.validate_row([ 'a', 'z', (1,2,3)]))
    nl()
    print("child table: find_all ['col2','y']             ", cht.find_all('col2', 'y' ))
    nl()
    print('Indexing attr col1 ... ')
    cht.index_attr('col1')
    display_table(cht)
    
    print("cht.length                 ", cht.length )
    print("cht.get_key(['a', 'z']     ", cht.get_key(['a', 'z']))
    print("cht.find_unique(['a', 'z'] ", cht.find_unique(['a', 'z']))
    print("cht.pop(['a', 'z'])        ", cht.pop(['a', 'z']))
    print("cht.length                 ", cht.length )
    nl()
    print("validate row [ 'a', 'z', (1,2,3)]", cht.validate_row([ 'a', 'z', (1,2,3)]))
    print("Note that tuple (1,2,3) passes as a str type, '(1,2,3)'.")
    nl()
    
    print('Child table get_row(3)', cht.get_row(3))
    nl()
    print('Child table get_rows(5)', cht.get_rows(5))
    nl()
    print('Child table get_rows([1,3])', cht.get_rows([1,3]))
    nl()
    
    print('Set child indexer instance')
    cht.set_indexer(Indexer)
    print('Index instance ', cht.indexer)
    nl()
    
    print('Simpe Index and Query')
    for cname in cht.column_names:
        cht.index_attr(cname)
    nl()
        
    print("(cht.index['col1']['a'] | ( cht.index['col2']['b']) & cht.index['col2']['y'] )")
    bmask = (cht.index['col1']['a'] | cht.index['col1']['b'] ) & cht.index['col2']['y'] 
    print('bmask ', bin(bmask))
    for tp in cht.get_rows(bmask):
        print(tp)
    nl()
 
    for db in [ tdb, tdb2 ]:
        db.clear_all()
        print('DB name ', db.dbname , ' is cleared.')
        for name, tbl in db.tables():
            print('Table ', name , ' cleared.  Len is ', tbl.length)
        nl()
        
    print('=== SubClassing ===')
    nl()
  
    
    class MyTable(TableStore):
    
        _tdef = TableDef(tname = 'MyRow', filename = 'mytable111', unique=['col1'],
                     col_defs = [ColDef(cname='col1', default=None, ptype=str),
                                 ColDef(cname='col2', default=0, ptype=int),
                                 ColDef(cname='col3', default=0.0, ptype=float),
                                 ColDef(cname='col4', default={}, ptype=dict)])
                                 
        def sum(self, col_name ):
            
            return sum(self.get_column(col_name))

 
    print('MyTable class _constructor ', MyTable._constructor())
    nl()  
 
                                 
    mt = MyTable()

    nl()
    print('mt instance table def ', mt.tdef)

    nl()
    print('dir(mt) ', dir(mt))
    nl()
    
    mt.extend([[ 'a', 1123, 7.3, {'hello':1, 'world':2}],
               [ 'b', 12423, 33.5, {'goodbye':999, 'world':777}],
               [ 'c', 523, 21.66, {'helloagain':999, 'yall':777}],
               [ 'd', 1123, 27.66, {'doitagain':111999, 'you\'all':777}]])


    print('Set mt indexer instance')
    mt.set_indexer(Indexer)
    print('Index instance ', mt.indexer)
    nl()
    print('Index Attrs', mt.column_names)

    print()
    for attr in mt.column_names:
        mt.index_attr(attr)
               
    display_table(mt)
    print()
    
    print('ListStore find functions')
    print("mt.find('col1', 'a')       ", mt.find('col1', 'a'))
    print("mt.get_row(0)              ", mt.get_row(0))
    print("mt.find_all('col2', 1123 ) ", mt.find_all('col2', 1123))
    print("mt.get_rows([0, 3])        ", mt.get_rows([0, 3]))
    print("mt.index['col2'][1123])    ", mt.index['col2'][1123], bin(mt.index['col2'][1123]))
    print("mt.get_rows(9) ->          ", mt.get_rows(9))
    print()
    
    print('sum of col2: ', mt.sum('col2')) 
    print('sum of col3: ', mt.sum('col3')) 
    nl()

    print('isinstance(mt, MyTable)    ', isinstance(mt, MyTable))
    print('isinstance(mt, TableStore) ', isinstance(mt, TableStore))
    print('isinstance(mt, TupleStore) ', isinstance(mt, TupleStore), '  # why ?')
    nl()
    
    print('THE END ')
    nl()
    
    
    import sys
 
    if mem_free_present:

        main_end = mem_free()
        print(f"=== Memory Usage for MicroPython on {sys.platform} ===")
        print('Total memory started: ', mem_start )
        print('Memory use to start of __main___ :', mem_start-main_start)
        print('Mem free at end: ', mem_free())
        print('Total memory used: ', mem_start-main_end)
        collect()
        print('Mem after collect: ',  mem_start-mem_free()) 
        nl()
        # print('locals ', locals())
    
    x = [tstore, tstore2, tdb, tdb2 ]   # hold reference for collect()    

"""
=== Memory Usage for MicroPython ESP32 ===
Total memory started:  8222544
Memory use to start of __main___ : 42048
Mem free at end:  8187840
Total memory used:  34704
Mem after collect:  24848

=== Memory Usage for MicroPython Pico ===
Total memory started:  149984
Memory use to start of __main___ : 45280
Mem free at end:  29312
Total memory used:  120672
Mem after collect:  25552
"""
    

