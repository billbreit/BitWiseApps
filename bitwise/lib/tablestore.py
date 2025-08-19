"""
module:     tablestore
version:    v0.4.4
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

tablestore - a small table store with relational functions based on 
    the liststore class extended with column types, unique keys, parent/child
    references between tables and persistence ( on demand ) using json.
    
    For *small datasets*, maybe a few hundred rows on limited-memory 
    micro-controllers.  200 rows X 200B/row ~= 40K, depending on qstr etc.

Example:

tdef = TableDef(tname = 'People', filename = 'people', unique=['name'],
                     col_defs = [ColDef(cname='name', default=None, ptype=str),
                                 ColDef(cname='address', default='<unknown>', ptype=str),
                                 ColDef(cname='phone', default='<unknown>' ptype=str),
ts = TableStore(tdef)


For example, a list of list for ['name', 'address', 'phone']:

people = [[ 'Bob', '733 Main Street', '123-456-7890' ],
          [ 'Mary', '22 Any Avenue', '123-456-2222' ],
          [ 'Sue', '11 My Way', '123-456-3333' ]]
          
ts.extend(people)

ts.get(['Mary'], 'address' ) would return '22 Any Avenue'              
ts.set(['Mary'], 'address', '444 Peyton Place' ) 
ts.get(['Mary'], 'address' ) would return '444 Peyton Place'                 
          
ts.get_key(['Bob']) would return ['Bob', '733 Main Street', '123-456-7890']

The ListStore and TupleStore base classes provide lower-level storage, access
and indexing. 
       
 - an indexing store for tuples. Note that indexer can consume 
   large amounts of memory and too memory-intensive for a 256K class platform.
   
 - a cross-platform version of namedlist.py, when Python dataclass is not available.
 
Known to run on Python 3.9+, micropython v1.20-22 on a Pico and Arduino Nano ESP32. 
    
"""

import os

import json
from collections import namedtuple, OrderedDict

try:
    from liststore import TupleStore, datetime, timestamp  # try abs
    print('abs path found')
except ImportError:
    from lib.liststore import TupleStore, datetime, timestamp

try:
    from core.fsutils import path_exists, path_separator
except ImportError:
    from lib.core.fsutils import path_exists, path_separator


"""TableDef - Table Definition,
     tname:str, used for tuple name, and if subclassed and used in db,
                appears as dbref.tname.  Good convention to make table
                class name the plural of tname.  
     filename:str,   filename.json
     unique:list[str],  column names
     col_defs:list[ColDef]
"""
TDef_fields = ['tname', 'filename',  'unique', 'col_defs']  # no _fields in mpy
TableDef = namedtuple('TableDef', TDef_fields)

"""ColDef - Column Definition,
     cname:str,
     default:[pytpe|None],  default of prype.  None means no default, 
              may need to fiddle ptype(default) -> error
     ptype:type, python type
"""
CDef_fields = [ 'cname', 'default', 'ptype' ]
ColDef = namedtuple('ColDef', CDef_fields )


class TableStoreError(Exception):
    pass

class TableStore(TupleStore):

    _tdef:TableDef = None   # If _tdef not None, TableStore is subclassed.
                            # If subclassed as part of db, db will use table
                            # subclass instance in _constructor method.
                            # Access any db table instance with either 
                            # db.table('tablename') or db.tablename

    
    def __init__(self, tdef:TableDef=None, db:'DataStore'=None ):
        """ Based on TupleStore with:
            - uniqueness constraints, assure unique key
            - python types, including namedtuple in columns, recoverable from JSON
            - JSON data store and recovery of non-JSON types, i.e. tuples
            
            - when used in DataStore (db not None), enforce referential integrity,
              parent/child key rels between tables.

        """

        if self._tdef is not None:  # use subclass _tdef, will override tdef
            self.tdef = self._tdef
        else:
            self.tdef = tdef
    
        col_names = [ c.cname for c in self.tdef.col_defs]
        defaults = [ c.default for c in self.tdef.col_defs]

        super().__init__(self.tdef.tname, col_names, defaults)
        
        self.ptypes:list[type] = [ c.ptype for c in self.tdef.col_defs]
        
        self.db:'DataStore' = db  # if TableStore used in DataStoreDef, table with parent/child key relations. 
        self._prelations:list[PRelation] = []  # as parent to child
        self._crelations:list[CRelation] = []  # as child to parent
    
    def __del__(self):
        """ Remove tangle of references, in mpy del is called by gc.collect"""
        
        self.db = None   # del circular ref.
        self._prelations = None  # table class instances
        self._crelations = None

    def _postinit(self):
        """Handle for db to late initialize, avoids forward/circular reference."""
    
        if self.db:
            # parent to child, answers table row children_exist ?
            self._prelations = [ PRelation( r.pcol, self.db.tabledict[r.child], r.ccol  )
                                    for r in self.db.relations if r.parent == self.tablename ]
            # child to parent, answers table row parents_exist ?
            self._crelations = [ CRelation( r.ccol, self.db.tabledict[r.parent], r.pcol  )
                                    for r in self.db.relations if r.child == self.tablename ]
    
    @classmethod
    def _constructor( cls ):
        """Returns a table def including a class instance of itself as
            ttype=class for db _constructor.  Means that TableSore is
            subclassed and has cls._tdef and probably a db reference.
            Note __del__ method. """  
        
        if cls._tdef is not None:  # is subclassed
            return DBTableDef( cls._tdef.tname, cls, cls._tdef.filename,
                                cls._tdef.unique, cls._tdef.col_defs)
 
                            
    @property
    def tablename(self) -> str:
        return self.tdef.tname

    @property   
    def filename(self) -> str:
        return self.tdef.filename      
    
    @property   
    def unique_columns(self) -> list[str]:
        return self.tdef.unique
        
    
    def keys(self) -> list[list]:
        """ Return list of key value lists, like [['John','Doe'],['Bob','Smith']]  """ 
        
        return [ self.make_key(row) for row in zip(*self.store)]
        

    """ Key Uniqueness Constraints """
    
    def is_duplicate(self, key:list) -> bool:
        """Key ( list of values forming key ) already exists. """
        
        if len(key) != len(self.unique_columns):
            raise TableStoreError(f'Key Error: length of key {key} must be {len(self.unique_columns)}.')
            
        if self.find_unique(key) > -1:
            return True
            
        return False
        
    def make_key(self, list_in:list) -> list:
        """Make unique key ( list of values ) from input list,
           probably as input for is_duplicate or find_unique query."""
        
        row_in = self.resolve_defaults(list_in)
    
        if len(row_in) != len(self.column_names):
            raise TableStoreError(f'Make Key: malformed list {list_in}')
    
        key_vals = [ row_in[self.slot_for_col(k)] for k in self.unique_columns ]

        return key_vals
    
        
    """ Validate Python Types, Unique Key, Parent References """
        
    def validate_row(self, row:list, add:bool=True ) -> list:
        """ Three part validation: types, key uniqueness and, if db,
            referential integrity - of two types, changed key or not.
              - add/ key change new val must have parents,
              - pop/ key change old val must not have children. """ 
    
        errors = []

        rrow = self.resolve_defaults(row)
    
        # types
        err_list = self.validate_types(rrow)
        if len(err_list) > 0:
            errors.extend(err_list)
        
        # uniqueness
        key = self.make_key(rrow)
        if add:
            if self.is_duplicate(key):
                errors.append(f"Validation Add Error: key '{key}' is duplicate.")
        else:
            if not self.is_duplicate(key):
                errors.append(f"Validation Update Error: key '{key}' does not exist.") 
        
        # referential integrity 
        err_list = self.validate_parents(rrow)
        if len(err_list) > 0:
            errors.extend(err_list)         
    
        return errors
    
    @staticmethod   
    def test_type( ptype, value ):
        """Generic type tester, will value pass type constructor,
           instance can be converted to target type, maybe incorrectly,
           tuple -> str for instance, may need str -> tuple parser. """
    
        try:
            if tuple in ptype.__bases__:  # is namedtuple
                x = ptype(*value)
            else:
                x = ptype(value)
        except Exception as e:
            raise TableStoreError(f"Bad Python Type: '{value}' is not {ptype}. {e} ")
            
        return x

    def check_column_types(self, col_name:str, col_values:list=None ) -> list:
        """Validate an entire column. Faster than validate_rows ? 
           If not col_vals, use col_name in table store"""
        
        if col_values is None:
            col_values = self.get_column(col_name)
            col_from_db = True
        else:
            col_from_db = False
        
        ptype = self.ptypes[self.slot_for_col(col_name)]
        
        err_list = []
        for val in col_values:
            try:
                self.test_type(ptype, val)
            except:
                err_list.append(f"Validation Error: value '{val}' must be type {ptype}")
        
        return err_list
        
    def validate_types(self, list_in:[list, tuple]) -> list:
        """Test a row of values against Python types for each column.
           If no errors, returned list will be empty.""" 

        if not isinstance(list_in, (list, tuple)) or list_in is None or list_in in [[],()]:
            raise TableStoreError('Invalid List: must provide list, not None or empty')
            
        err_list = []
        for pt, v in zip(self.ptypes, list_in):
            try:
                self.test_type(pt, v)
            except TableStoreError as e:
                err_list.append(f"Validation Error: value '{v}' must be type {pt}")
                
        return err_list
        
    def fix_types(self, data:list, resolve_namedtuples:bool = False ) -> list:
        """Restore Python types from JSON.  Resolve namedtuples, that is tuple -> namedtuple."""
    
        for col, pt in zip(self.column_names, self.ptypes):

            if pt is tuple or tuple in pt.__bases__:
                sl = self.slot_for_col(col)
                
                for i, _  in enumerate(data):
                    if resolve_namedtuples and tuple in pt.__bases__:
                        data[i][sl] = pt(*data[i][sl])
                    else:
                        data[i][sl] = tuple(data[i][sl])
            # other types ?
                    
        return data
        
    """ Integrity Constraints """
    
    def validate_parents(self, row:list) -> list:
        """Table row child -> parents rel. No add without parents.
           Row is in relation as child is to parent, use _crelations"""
                
        errors = []
  
        if self.db:
            rrow = self.resolve_defaults(row)
            for ccol, par, pcol in self._crelations:
 
                pkey = rrow[self.slot_for_col(ccol)]
                
                if par.find(pcol, pkey) < 0:   # may be unique or not, need compund key ? 
                    errors.append(f"Invalid Parent Key: key '{pkey}' has no parent key in {par.tablename} table") 
                    
        return errors
        
    def parents_exist(self, row:list ) -> bool:
        """Child not having *required* parents is always an error.
         If all parents exist or no parents required, return True."""
        
        errs = self.validate_parents( row )
        if len(errs) > 0:
            return False
        return True
            
    def validate_children(self, row:list) -> list:
        """ Table row parent -> children rel. More like a find_children function.
            No error unless pop/remove of parent with children.
            Row is in relation as parent is to child, use _prelations. """
        
        info = []


        if self.db:
            rrow = self.resolve_defaults(row)
            for pcol, child, ccol in self._prelations:

                ckey = rrow[self.slot_for_col(pcol)]
                num_ch = len(child.find_all(ccol, ckey))
                
                if num_ch > 0:   # has children 
                    info.append(f"Child Key Dependency: key '{ckey}' has {num_ch} children in {child.tablename} table.") 
                    
        return info
        
    def children_exist(self, row:list ) -> bool:
        """Row has dependent rows in child tables, is error if parent being row popped/removed.  """ 
        
        info = self.validate_children( row )
        if len(info) > 0:
            return True
        return False
        
    """Retrieve Rows/Columns """ 

    def get(self, key:list, col_name:str ):
        """Get value in a column with unique key, return value.  """
        
        if isinstance(key, str): key = [key]
    
        return super().get(self.find_unique(key), col_name)
        
    def fetch_key(self, key:list ) -> tuple:
        """Find unique_row and pass slot to fetch row, resetting changed bit for row""" 
    
        slot = self.find_unique(key)
        
        if slot < 0:
            raise TableStoreError(f"Get Key Error: key '{key}' not found in {self.tablename}.") 
    
        return super().fetch_row(slot)
        
        
    def get_key(self, key:list, asdict:bool=False ) -> tuple:
        """ Get row with unique key, return tuple of values."""

        slot = self.find_unique(key)
        
        if slot < 0:
            raise TableStoreError(f"Get Key Error: key '{key}' not found in {self.tablename}.") 
    
        return super().get_row(slot, asdict)

            
    """Update Methods,
        - check uniqueness of keys
        - validate Python types
        - check references if table is part of a DataStore
            - no row add without parent keys
            - no row remove when existing children
    """ 
        
    def set(self, key:list, col_name:str, value ):
        """Set col_name (attr) in slot int to value.  If key val altered,
            validation is equivalent to a row delete and add.   """
        
        
        rrow = list(self.get_key(key)) # need to de-tuple   
        
        if col_name in self.unique_columns:  # equivalent to rename (delete/add ) row
            key_changed = True
            ch_list = self.validate_children(rrow)
        
            if len(ch_list) > 0:
                raise TableStoreError(f"Set Error; column {col_name} '{key}' has dependent children. {ch_list}.")
        else:
            key_changed = False 
                    
        rrow[self.slot_for_col(col_name)] = value
        
        err_list = self.validate_row(rrow, add=key_changed)
        
        if len(err_list) > 0:
            raise TableStoreError(f"Set Error: Invalid value {value} for {col_name}: ", err_list)
            
        super().set(self.find_unique(key), col_name, value )


    def append(self, list_in:list=None ):
        """Append to store a row/list."""
    
            
        err_list = self.validate_row(list_in)
        
        if len(err_list) > 0:
            raise TableStoreError('Append: Invalid List: ', err_list)
            
        super().append(list_in)
        
    def extend(self, list_of_lists:list=None):
        """Extend store with list of lists/rows.  Something like a transaction,
           if one fails, all fail. """ 
    
        if list_of_lists is None or len(list_of_lists)==0:
            raise TableStoreError('Extend - list passed can not be None or empty.')
            
        # test list for duplicates
        unique_keys = { tuple(self.make_key(r)) for r in list_of_lists }
        if len(unique_keys) != len(list_of_lists):
            raise TableStoreError('Extend - duplicate keys within input list.') 
    
        err_list = [ e for e in map(self.validate_row, list_of_lists) if e ]  # if e != []

        if any(err_list):
            raise TableStoreError('Extend - invalid rows, no update: ', err_list)
            
        super().extend(list_of_lists)

        
    def pop(self, key:list ) -> tuple:
        """Remove row from TableStore and return row.  Do not allow pop if parent
            row has existing children in related tables. """
        
        rrow = self.get_key(key)
        ch_list = self.validate_children(rrow)
        
        if len(ch_list) > 0:
            raise TableStoreError(f"Pop Error: key '{key}' has dependent children. {ch_list}.")  
        
        row = super().pop(self.find_unique(key))
        
        return row
        
    def rename(self, oldkey:list, newkey:list ):
        """Rename row unique key and keys in dependent children. Needed ? """ 
        
        pass
            
        
    """ Find Methods """
        
    def find_unique( self, unique_key:list ) -> int:
        """Return a slot for a row matching list of values in unique key columns.
           Uses first key slot for store.index search """ 
           
        
        if isinstance(unique_key, str): unique_key = [key]
        
        if len(unique_key) != len(self.unique_columns):
            raise TableStoreError(f"Find Unique: misformed key '{unique_key}', must have {len(self.unique_columns)} columns." )
    
        key_slots =[ self.slot_for_col(k) for k in self.unique_columns ]
            
        slot_index = key_slots[0]  
        
        value = unique_key[0]
        start = 0
        i = 0

        while i > -1:
            try:
                i = self.store[slot_index].index(value, start)
                start = i + 1
            except ValueError as ve:
                i = -1
            else:
                matches = True
                for ks, val in zip(key_slots, unique_key):
                    if self.store[ks][i] != val:
                        matches = False
                            
                if matches == True:
                    return i  # > -1
        return i   # -1

        
    """Save/Load Methods
        Note the flow of control for db refs:
          table method -> db method -> table method with full path """
        
    def dump(self, resolve_types:bool = False ) -> list[tuple]:
        """Create list of named tuples.
           If resolve_types, then convert base tuple to namedtuple in column
           of type namedtuple.  Not for JSON storage, yet. """
    
        data = [ list(row) for row in zip(*(self.store))]
        
        if resolve_types:
            data = self.fix_types(data, resolve_types)
            
        yield from [ self.ntuple_factory(*tup) for tup in tuple(data)]
            
        
    def load(self, filename:str=None ):
        """Load TableStore from JSON """
 
        # db will re-call table.load and provide full 'dir/filename' path
        if self.db and not filename and filename != self.filename:
            self.db.load_all()
    
        if filename:
            fname = filename + ".json"
        else:
            fname = self.filename + ".json"
        
        with open( fname, "rt") as jfile:
            data = json.load(jfile)
        
        data = self.fix_types(data)
            
        self.extend(data)   # slow, with validation

        
    def save(self, filename:str=None):
        """Save TableStore or, trigger db.save_all and eventually this table
           save, to a JSON file."""
        
        # db will re-call table.save providing full 'db_dir/filename' path
        if self.db and not filename and filename != self.filename:
            self.db.save_all() 
    
        data = self.dump()
        
        if filename:
            fname = filename + ".json"
        else:
            fname = self.filename + ".json"

        with open( fname, "wt") as jfile:
            json.dump([ list(d) for d in data ], jfile)
            


"""DataStore Structure Definitions """
            
""" DBDef, DataStore Definition -
      dbname:str,
      dirname:str,
      relations:list[RelationDef],
      table_defs:list[TableDef], TableDef subclasses, in parent->child db load order
"""
DBDef_fields = ['dbname', 'dirname', 'relations', 'table_defs']  # mpy has no _fields method
DataStoreDef = namedtuple('DataStoreDef', DBDef_fields )

"""DBTableDef - Table Definition for DB based on TableDef, for db, not the user
     tname:str,
     ttype:TableStore or subclass    # added to allow subclassing
     filename:str,
     unique:list[str],
     col_defs:list[ColDef]
"""
DBTDef_fields = ['tname', 'ttype', 'filename',  'unique', 'col_defs']  
DBTableDef = namedtuple('DBTableDef', DBTDef_fields)

""" RelDef, Relation Definition - parent/pcol <-> child/ccol
      parent:str,
      pcol:str,
      child:str,
      ccol:str
""" 
# RelDef_fields = [ 'parent', 'pcols', 'child', 'ccols' ]  map list of cols
RelDef_fields = [ 'parent', 'pcol', 'child', 'ccol' ]  # map single col
RelationDef = namedtuple('RelationDef', RelDef_fields )   # from one to many

""" Parent  Relation, is parent of child, embedded in table - no delete if existing children
      pcol:str,
      child:TableStore,  # looking down from one to many
      ccol:str
"""
# PRel_fields = [ 'pcols', 'child', 'ccols' ]  map list pcols to list of col names
PRel_fields = [ 'pcol', 'child', 'ccol' ]    # map single name to col, db id phase 2 ?
PRelation = namedtuple('PRelation', PRel_fields ) 

""" Child Relation, is child of parent, embedded in table - no add without existing parent
      ccol:str,
      parent:TableStore,   # looking up from many to one
      pcol:str
"""
# CRel_fields = [ 'ccols', 'parent', 'pcols' ]   ditto above
CRel_fields = [ 'ccol', 'parent', 'pcol' ]
CRelation = namedtuple('CRelation', CRel_fields )


class DataStoreError(Exception):
    pass

class DataStore(object):
    """Multi-table collection, has some features of a relational database.  
       In fact, it's more a relational database than a "data store" per se,
       but using the term DataStore may avoid a bit of confusion.
            
        - build referential integrity tables embedded into TableStore instances.
            - no delete for parent with children
            - no add for child without parent
        - clear all tables in datastore
        - clear all changed masks
        - load/save of individual table triggers db load/save.
        - and missing lots of things 'real' databases have ...  """
        
    _dbdef:DataStoreDef = None  # for subclassing, table_defs will be a list
                                # of TableStore subclasses, not str table names,
                                # must be subclass like [ TableClass1, TableClass2 ]
                                # in parent -> child 'topological' load order.

    def __init__(self, dbdef:DataStoreDef=None ):
    
        if self._dbdef is not None:
            # rewrite table_defs from class instances to DBTableDef tuples
            
            tdefs = [ tclass._constructor() for tclass in self._dbdef.table_defs ]
              
            self.dbdef = DataStoreDef( self._dbdef.dbname, self._dbdef.dirname,
                         self._dbdef.relations, tdefs ) 
        else:
            self.dbdef = dbdef

        if len({ tdef.tname for tdef in self.dbdef.table_defs }) != len([ tdef.tname for tdef in self.dbdef.table_defs ]):
            raise DataStoreError('DataStoreDef contains duplicate tables.')
        
        self.tabledict = OrderedDict()  # for mpy to maintain order, must load par->child
        for tdef in self.dbdef.table_defs:
            self.tabledict[tdef.tname] = tdef.ttype(tdef, self)
        
        for tobject in self.tabledict.values():
            tobject._postinit()  # embeds parent->child and child->parent rels into tables
        
        # set attrs for table name/table instance, used for queries.  For ex. 
        # db.Customer is short hand for db.table('Customer'), of table class Customers    
        for n, v in self.tabledict.items():
            if n not in dir(self):
                setattr(self, n, v)
            else:
                raise DataStoreError(f'Table name {n} conflicts with a DataStore attr. name.') 
        
        if not path_exists(self.dbdef.dirname):
            os.mkdir(self.dbdef.dirname)

    def __del__(self):
        """ Remove tangle of references, in mpy del is called by gc.collect"""
        
        self.dbdef = None   # external table class refs.
        self.tabledict = None  # table instances, may be external refs. 
                               # from x = db.table('str') which is bad for gc
       
            
    @property
    def dbname(self):
        return self.dbdef.dbname

    @property       
    def dirname(self):
        return self.dbdef.dirname

    @property       
    def relations(self):
        return self.dbdef.relations
    
    @property       
    def tabledefs(self):
        return self.dbdef.table_defs
        
    def table(self, name:str) -> TableStore:
        return self.tabledict[name]
        
    def tables(self) -> list[tuple[str, TableStore]]:
        return self.tabledict.items()
        
    def tables_changed(self) -> list[str]:
        return [ tn for tn, ti in self.tabledict.items() if ti.rows_changed() > 0 ]
        
    def reset_all(self):
        """Reset all changed masks in tables""" 
    
        for tname, tobj in self.tables():
            tobj.reset_changed()
        
    def clear_all(self):
        """Empty tables, reset index and changed mask"""
    
        for tname, tobj in self.tables():
            tobj.clear()
        
    def load_all(self):
    
        for tname, tobj in self.tables():
            fullname = path_separator().join([self.dirname, tname])
            tobj.load(fullname)
        
    def save_all(self):
    
        for tname, tobj in self.tables():
            fullname = path_separator().join([self.dirname, tname]) 
            tobj.save(fullname)

def display_table( tstore ):
    # print('Store type  ', type(tstore))
    print('Table name  ', tstore.tablename)
    print('Filename    ', tstore.filename)
    print('Unique      ', tstore.unique_columns)
    print()
    print('Length      ', tstore.length)
    for attr, col_store in zip(tstore.column_names, tstore.store):
        print('Column ', attr, col_store)
    print()
    if tstore.index:
        print("Index ")
        for k, subdict in tstore.index.items():
            print(k, subdict)
        print()
    print('Columns changed ', [bin(i) for i in tstore.changed])
    print('Rows changed   ', bin(tstore.rows_changed()) )
    print()

    
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

