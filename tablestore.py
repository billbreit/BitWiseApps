"""
tablestore - a small table store with relational functions based on 
    the liststore class extended with column types, unique keys, parent/child
    references between tables and persistence using json. 

module:     tablestore
version:    v0.4.1
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

An Example:

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

The ListStore and TupleStore base classes also provide lower-level access and indexing. 
	   
 - an indexing store for tuples. Note that indexer can consume 
   large amounts of memory and too memory-intensive for a 256K class platform.
   
 - a cross-platform version of namedlist.py, when Python dataclass is not available.
 
Known to run on Python 3.9, micropython v1.20-22 on a Pico and Arduino Nano ESP32. 
	
"""

try:
	from gc import mem_free, collect
	gc_present = True
	mem_start = mem_free()
except:
	gc_present = False

import os

import json
from collections import namedtuple, OrderedDict

from liststore import TupleStore

# utils

def isdir(path:str) -> bool:
    try:
        mode = os.stat(path)[0]
        return mode & 0o040000
    except OSError:
        return False


def isfile(path:str) -> bool:
    try:
        return bool(os.stat(path)[0] & 0x8000)
    except OSError:
        return False


"""TableDef - Table Definition,
     tname:str,
     filename:str,
     unique:list[str],
     col_defs:list[ColDef]
"""
TDef_fields = ['tname', 'filename',  'unique', 'col_defs']  # no _fields in mpy
TableDef = namedtuple('TableDef', TDef_fields)

"""ColDef - Column Definition,
     cname:str,
     default:[pytpe|None],  # None means no default, may need to fiddle ptype(default) -> error
     ptype:type
"""
CDef_fields = [ 'cname', 'default', 'ptype' ]
ColDef = namedtuple('ColDef', CDef_fields )


class TableStoreError(Exception):
	pass

class TableStore(TupleStore):

	
	def __init__(self, tdef:TableDef, db:'DataStore'=None ):
		""" Based on TupleStore with:
			- uniqueness constraints, assure unique key
			- python types, including namedtuple in columns, recoverable from JSON
			- JSON data store and recovery of non-JSON types, i.e. tuples
			
			- when used in DataStore (db not None), enforce referential integrity,
			  parent/child key rels between tables.

		"""

		self._tdef = tdef
	
		col_names = [ c.cname for c in tdef.col_defs]
		defaults = [ c.default for c in tdef.col_defs]

		super().__init__(tdef.tname, col_names, defaults)
		
		self.ptypes:list[type] = [ c.ptype for c in tdef.col_defs]
		
		self.db:'DataStore' = db  # if TableStore used in DataStoreDef, table with parent/child key relations. 
		self._prelations:list[PRelation] = []  # as parent to child
		self._crelations:list[CRelation] = []  # as child to parent

	def _postinit(self):
		"""Handle for db to late initialize, avoids forward/circular reference."""
	
		if self.db:
			# parent to child, answers table row children_exist ?
			self._prelations = [ PRelation( r.pcol, self.db.tabledict[r.child], r.ccol  )
									for r in self.db.relations if r.parent == self.tablename ]
			# child to parent, answers table row parents_exist ?
			self._crelations = [ CRelation( r.ccol, self.db.tabledict[r.parent], r.pcol  )
									for r in self.db.relations if r.child == self.tablename ]
							
	@property
	def tablename(self):
		return self._tdef.tname

	@property   
	def filename(self):
		return self._tdef.filename      
	
	@property   
	def unique(self):
		return self._tdef.unique
		
	
	def keys(self) -> list[tuple]:
		""" Return list of key value lists, like [['John','Doe'],['Bob','Smith']]  """ 
		
		return [ self.make_key(row) for row in zip(*(self.store))]


	""" Uniqueness Constraints """
	
	def is_duplicate(self, key:list) -> bool:
		"""Key ( list of values forming key ) already exists. """
		
		if len(key) != len(self.unique):
			raise TableStoreError(f'Validation Error - length of key not equal to length of unique key')
			
		if self.find_unique(key) > -1:
			return True
			
		return False
		
		
	""" Validate Python Types, Unique Key, Parent References """
		
	def validate_row(self, row:list, add:bool=True ) -> list:
		""" Three part validation: types, key uniqueness and, if db,
		    referential integrity - of two types.
		      - add must have parents,
		      - pop must not have children. """ 
	
		errors = []
	
		# types
		err_list = self.validate_types(row)
		if len(err_list) > 0:
			errors.extend(err_list)
		
		# uniqueness
		key = self.make_key(row)
		if add:
			if self.is_duplicate(key):
				errors.append(f"Validation Add Error: key '{key}' for row {row} is duplicate.")
		else:
			if not self.is_duplicate(key):
				errors.append(f"Validation Update Error: key '{key}' for row {row} does not exist.") 
		
		# referential integrity	
		err_list = self.validate_parents(row)
		if len(err_list) > 0:
			errors.extend(err_list)			
	
		return errors

		
	def validate_types(self, list_in:list) -> list:
		"""Test a row of values value against Python type for columns.
		   If no errors, returned list will be empty.""" 

		if not isinstance(list_in, list) or list_in is None or list_in==[]:
			raise TableStoreError('Invalid List - list passed can not be None or empty')
			
		err_list = []
		for pt, v in zip(self.ptypes, list_in):
			try:
				if tuple in pt.__bases__:  # is namedtuple
					x = pt(*v)
				else:
					x = pt(v)               
			except:
				err_list.append(f"Validation Error: value '{v}' must be type {pt}")
				
		return err_list
		
	def fix_types(self, data:list, resolve_namedtuples:bool = False ) -> list:
		"""Restore Python types from JSON.  Resolve namedtuples, that is tuple -> namedtuple """
	
		for col, pt in zip(self.col_names, self.ptypes):

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

		# CRel_fields = [ 'ccol', 'parent', 'pcol' ]
				
		errors = []
		
		if self.db:
			for ccol, par, pcol in self._crelations:

				pkey = row[self.slot_for_col(ccol)]
				
				if par.find(pcol, pkey) < 0:   # may be unique or not, need compund key 
					errors.append(f"Invalid Parent Key: key '{pkey}' in row {row} has no parent key in {par.tablename} table") 
					
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
			 
		# PRel_fields = [ 'pcol', 'child', 'ccols' ]
		
		info = []
		
		if self.db:
			for pcol, child, ccol in self._prelations:

				ckey = row[self.slot_for_col(pcol)]
				num_ch = len(child.find_all(ccol, ckey))
				
				if num_ch > 0:   # has children 
					info.append(f"Child Key Dependency: key '{ckey}' in row {row} has {num_ch} children in {child.tablename} table") 
					
		return info
		
	def children_exist(self, row:list ) -> bool:
		"""Row has dependent rows in child tables, is error if parent being row popped/removed.  """ 
		
		info = self.validate_children( row )
		if len(info) > 0:
			return True
		return False
		
	"""Retrieve Rows """ 

	def get(self, key:list, col_name:str ):
		"""Get value of col_name in slot, return value  """
		
		return super().get(self.find_unique(key), col_name)
		
	def get_key(self, key:list ) -> tuple:
		""" Use unique list of key values to retrieve row. """
	
		slot = self.find_unique(key)
		
		if slot < 0:
			raise TableStoreError(f'Get key error, slot for key {key} not found ') 
	
		return super().get_row(slot)
		

			
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
		
		if col_name in self.unique:  # equivalent to rename (delete/add ) row
			key_changed = True
			ch_list = self.validate_children(rrow)
		
			if len(ch_list) > 0:
				raise TableStoreError(f"Set Error; column {col_name} in key '{key}' has dependent children. {ch_list}.")
		else:
			key_changed = False	
					
		rrow[self.slot_for_col(col_name)] = value

		# err_list = self.validate_row(rrow, add=True if key_changed else False)		
		err_list = self.validate_row(rrow, add=key_changed)
		
		if len(err_list) > 0:
			raise TableStoreError(f"Set Error: Invalid value {value} for {col_name}: ", err_list)
			
		super().set(self.find_unique(key), col_name, value )


	def append(self, list_in:list=None ):
		"""Append to store a row/list."""
	
			
		err_list = self.validate_row(list_in)
		
		if len(err_list) > 0:
			raise TableStoreError('Append - Invalid List: ', err_list)
			
		super().append(list_in)
		
	def extend(self, list_of_lists:list=None):
		"""Extend store with list of lists/rows.  Something like a transaction,
		   if one fails, all fail. """ 
		   
		print('extending ... ', list_of_lists)
	
		if list_of_lists is None or len(list_of_lists)==0:
			raise TableStoreError('Extend - list passed can not be None or empty.')
			
		# list for duplicates
		unique_keys = { tuple(self.make_key(r)) for r in list_of_lists }
		if len(unique_keys) != len(list_of_lists):
			raise TableStoreError('Extend - duplicate keys within input list.') 

		validation_errs = []

		for list_in in list_of_lists:
		
			err_list = self.validate_row(list_in)
		
			if len(err_list) > 0:
				validation_errs.extend(err_list)
			
		if len(validation_errs) > 0:
			raise TableStoreError('Extend - invalid rows, no update: ', validation_errs)
			
		super().extend(list_of_lists)
		
	def pop(self, key:list ) -> tuple:
		"""Remove row from TableStore and return row.  Do not allow pop if parent
			row has existing children in related tables. """
		
		rrow = self.get_key(key)
		ch_list = self.validate_children(rrow)
		
		if len(ch_list) > 0:
			raise TableStoreError(f"Error Popping key '{key}'. Has dependent children. {ch_list}.")  
		
		row = super().pop(self.find_unique(key))
		
		return row
			
		
	""" Find Methods """
	
	def make_key(self, list_in:list) -> list:
		"""Make unique key ( list of values ) from input list,
		   probably as input for is_duplicate or find_unique query."""
		
		row_in = self.resolve_defaults(list_in)
	
		if len(row_in) != len(self.col_names):
			raise TableStoreError(f'Make key: malformed list {list_in}')
	
		key_vals = [ row_in[self.slot_for_col(k)] for k in self.unique ]

		return key_vals
		
	def find_unique( self, unique_key:list ) -> int:
		"""Return a slot for a row matching list of values in unique key columns.
		   Uses first key slot for store.index search """ 
		
		if len(unique_key) != len(self.unique):
			raise TableStoreError(f'Find_Unique: misformed key, must have {len(self.unique)} columns.' )
	
		key_slots =[ self.slot_for_col(k) for k in self.unique ]
			
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

		
	"""Save/Load Methods """
		
	def dump(self, resolve_types:bool = False ) -> list[tuple]:
		"""Create list of named tuples.
		   If resolve_types, then convert base tuple to namedtuple in column
		   of type namedtuple.  Not for JSON storage, yet. """
	
		data = [ list(row) for row in zip(*(self.store))]
		
		if resolve_types:
			data = self.fix_types(data, resolve_types)
			
		return [ self.ntuple_factory(*tup) for tup in tuple(data)]
			
		
	def load(self, filename:str=None ):
		"""Load TableStore from JSON """
		
		if self.db and not filename:
			self.db.load_all()  # db will call save and provide full 'dir/filename' path
	
		if filename:
			fname = filename + ".json"
		else:
			fname = self.filename + ".json"
		
		with open( fname, "r") as jfile:
			data = json.load(jfile)
		
		data = self.fix_types(data)
			
		self.extend(data)

		
	def save(self, filename:str=None):
		"""Save TableStore to JSON."""
		
		if self.db and not filename:
			self.db.save_all()  # db will re-call table.save providing full 'dir/filename' path
	
		data = self.dump()
		
		if filename:
			fname = filename + ".json"
		else:
			fname = self.filename + ".json"

		with open( fname, "w") as jfile:
			json.dump([ list(d) for d in data ], jfile)
			


"""DataStore Structure Definitions """
			
""" DBDef, DataStore Definition -
	  dbname:str,
	  dirname:str,
	  relations:list[RelationDef],
	  table_defs:list[TableDef]
"""
DBDef_fields = ['dbname', 'dirname', 'relations', 'table_defs']  # mpy has no _fields method
DataStoreDef = namedtuple('DataStoreDef', DBDef_fields )

""" RelDef, Relation Definition -
	  parent:str,
	  pcols:str,
	  child:str,
	  ccol:str
""" 
# RelDef_fields = [ 'parent', 'pcols', 'child', 'ccols' ]  map list of cols
RelDef_fields = [ 'parent', 'pcol', 'child', 'ccol' ]  # map single col
RelationDef = namedtuple('RelationDef', RelDef_fields )   # from one to many

""" Parent  Relation, is a parent to child, embedded in table - no delete if existing children
	  pcol:str,
	  child:TableStore,  # looking down from one to many
	  ccol:str
"""
# PRel_fields = [ 'pcols', 'child', 'ccols' ]  map list pcols to list of col names
PRel_fields = [ 'pcol', 'child', 'ccol' ]    # map single name to col, phase 1 ?
PRelation = namedtuple('PRelation', PRel_fields ) 

""" Child Relation, is child to parent, embedded in table - no add without existing parent
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
	   but using the term DataStore may avoid confusion.
	        
	    - build referential integrity tables embedded into TableStore instances.
	        - no delete for parent with children
			- no add for child without parent
		- clear all tables in datastore
		- load/save of individual table triggers db load/save.
		- and missing lots of things 'real' databases have ...	"""

	def __init__(self, dbdef:DataStoreDef ):
	
		self.dbdef = dbdef

		if len({ tdef.tname for tdef in dbdef.table_defs }) != len([ tdef.tname for tdef in dbdef.table_defs ]):
			raise DataStoreError('DataStoreDef contains duplicate tables')
		
		self.tabledict = OrderedDict()  # maintain order, must load top-down
		for tdef in dbdef.table_defs:
			self.tabledict[tdef.tname] = TableStore(tdef, self)
		
		for tobject in self.tabledict.values():
			tobject._postinit()  # embeds parent->child and child->parent rels into tables
		
		if not isdir(dbdef.dirname):
			os.mkdir(dbdef.dirname)
			
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
		
	def tables(self) -> list[TableStore]:
		return self.tabledict.items()
		
	def clear_all(self):
	
		for tname, tobj in self.tables():
			tobj.clear()
		
	def load_all(self):
	
		for tname, tobj in self.tables():
			fullname = '/'.join([self.dirname, tname])
			# print('loadall ', fullname)
			tobj.load(fullname)
		
	def save_all(self):
	
		for tname, tobj in self.tables():
			fullname = '/'.join([self.dirname, tname]) 
			tobj.save(fullname)

def display_table( tstore ):
	print('Store type  ', type(tstore))
	print('Table name  ', tstore.tablename)
	print('Length      ', tstore.length)
	# nl()
	for attr, col_store in zip(tstore.col_names, tstore.store):
		print('Column ', attr, col_store)
	nl()
	print('Index ')
	for k, subdict in tstore.index.items():
		print( k, subdict )
	nl()
	print('Columns changed ', tstore.changed )
	print('Rows changed   ', bin(tstore.rows_changed()) )
	nl()
	# print('Rows changed indexes ', bit_indexes(lstore.rows_changed()))
	# print('Rows deleted   ', bin(lstore._deleted)) 			


if __name__ == '__main__':

	nl = print
	
	nl()
	print('=== Test of TableStore/DataStore Classes ===')
	nl()
	
	if gc_present:
		main_start = mem_free()
		collect()   # makes pcio/esp32 more consistent

	"""
	MyTuple = namedtuple('MyTuple', [ 'x', 'y', 'z'])
	nl()
	print('MyTuple', MyTuple)
	print('dir    ', dir(MyTuple))
	nl()
	myt = MyTuple(2, 3, 4)
	print('myt    ', myt)
	print('dir    ', dir(myt))
	print('myt.__class__ ', myt.__class__)
	print('dir     ', dir(myt.__class__))
	nl()
	"""
	
	# print(myt.__bases__)
	
	MyTuple = namedtuple('MyTuple', [ 'x', 'y', 'z'])
	DateTime = namedtuple('DateTime', [ 'year', 'month', 'day', 'hour', 'min', 'secs' ])
	
	tdef = TableDef(tname = 'Test', filename = 'testing111', unique=['col1','col2'],
					 col_defs = [ColDef(cname='col1', default=None, ptype=str),
								 ColDef(cname='col2', default=0, ptype=int),
								 ColDef(cname='col3', default=0.0, ptype=float),
								 ColDef(cname='col4', default={}, ptype=dict),
								 ColDef(cname='col5', default=[], ptype=list),
								 ColDef(cname='col6', default=(0, 0, 0), ptype=tuple),
								 ColDef(cname='col7', default=(0, 0, 0), ptype=MyTuple),
								 ColDef(cname='col8', default=False, ptype=bool)]
					)
	
	print('== TableDef ==')
	for n, l in zip(TDef_fields, tdef):
		print(n, ': ', l)
	nl()
	
	tstore = TableStore(tdef )
	
	print('dir(store) ', dir(tstore))
	
	print('Extend tstore with errors ')
	nl()
	
	try:
		tstore.extend([['a', 'b', 'c'],
					['d', 'e', 'f'],
					['g', 'h', 'i']])
	except Exception as e:
		print(e)
		nl()

	tstore.extend([['a', 2, 1, {'d': 'testing'}, ['aaa', 'bbb', 'ccc' ], ( 4, 4, 4 ), ( 7, 8, 9 ), True ],
					['d', 4, 2.2],
					['g', -2],
					['kk', 77]])
					
	for t in iter(tstore):
		print(t)
	nl()
	
	tstore.reset_changed()
		
	tstore.set(['a', 2 ], 'col3', 77.77)
	tstore.set(['kk', 77], 'col7', ( 12, 11, 10 ))
	
	tstore.append(['LLL', 230, 22, {'aaa':None, 'BBB':123}, ['List of stuff', 'More stuff' ], ( 3, 4, 5 ), (1, 1, 1 ), True])
	try:
		tstore.append(['LLL', 230, 22, {'aaa':None, 'BBB':123}, [333], ( 3, 4, 5 )])  # -> error
	except Exception as e:
		print('Appending ... is_duplicate: ', e )
	nl()
	tstore.append(['MMM', 6 ])
	tstore.append(['MMM', 3 ])
	
	tstore.index_attr('col1')
	tstore.index_attr('col7')

	nl()
	print('=== Display TStore ===')
	display_table(tstore)
	nl()
	
	for t in iter(tstore):
		print(t)
	nl()
	
	print("is_duplicate(['MMM', 0] ", tstore.is_duplicate(['MMM', 0]))
	print("is_duplicate(['NNN', 5] ", tstore.is_duplicate(['NNN', 5]))
	
	
	
	print("find_unique(['a', 0] ", tstore.find_unique(['a', 0]))
	print("find_unique(['LLa', 230] ", tstore.find_unique(['LLa', 230]))
	print("find_unique(['d', 4] ", tstore.find_unique(['d', 4]))
	nl()
		
	tstore.set(['d', 4 ], 'col2', 999 )
	tstore.set(['g', -2 ], 'col4', {'a':0})

	sl = tstore.find_unique(['d', 999])
	print("Get row ['d', 999]", tstore.get_key(['d', 999]))
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
	print('Dump - resolve types ( col7 tuple -> MyTuple )')
	for r in tstore2.dump(resolve_types=True):
		print(r)
	nl()
	
	# print(tstore2.find_unique(['a', 'c']))
	
	keys = tstore2.keys()
	print('keys ', keys )
	
	print('=== DataStore ===')
	nl()
	

	dbdef = DataStoreDef(
				dbname = 'Test' , dirname = 'testdata',
				relations = [ RelationDef( 'partable1', 'col1', 'chtable', 'col1'),
						      RelationDef( 'partable2', 'col1', 'chtable', 'col2')],
						   
				table_defs = [ TableDef( 'partable1',
									filename = 'partable1', unique = ['col1'],
									col_defs = [ColDef(cname='col1', default='', ptype=str),
												ColDef(cname='col2', default='', ptype=str)]),
															 
								TableDef( 'partable2',
									 filename = 'partable2', unique = ['col1'],
									 col_defs = [ColDef(cname='col1', default='', ptype=str),
												 ColDef(cname='col2', default='', ptype=str)]),
															 
								TableDef( 'chtable',
									 filename = 'chtable', unique = ['col1','col2'],
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
		
	
	nl()
	print(dir(DataStore))
	nl()
	tdb = DataStore(dbdef)
	print(tdb)
	nl()
	for n, t in tdb.tables():
		print('table ', n, t )
		print('par ', t._prelations)
		print('ch  ', t._crelations)
		
	p1 = [	[ 'a', 'test a '],
			[ 'b', 'test b '],	
			[ 'c', 'test c ']]
					
	tdb.table('partable1').extend(p1)
	
	p2 = [	[ 'x', 'test x '],
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
	
	cht = tdb.table('chtable')
	
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
	
	
	tdb.save_all()
	tdb2 = DataStore(dbdef)
	tdb2.load_all()
	

	par2t = tdb2.table('partable2')
	cht = tdb2.table('chtable')
	print('parents_exist      ', par2t.parents_exist([ 'a', 'mmm', 'testing a.z']), ' -> problem, has no parents, so has required parents is True')
	print('children_exist     ', par2t.children_exist([ 'x', 'mmm', 'testing a.z']))
	print('val children     ', par2t.validate_children([ 'y', 'mmm', 'testing a.z']))
	print('find_all in child', cht.find_all('col2', 'y' ))
	print('val parents      ', cht.validate_parents([ 'm', 'n', 'testing a.z']))
	print('validate row     ', cht.validate_row([ 'a', 'z', (1,2,3)]))
	nl()
	
	cht.index_attr('col1')
	display_table(cht)
	
	print("cht.length             ", cht.length )
	print("cht.get_key(['a', 'z'] ", cht.get_key(['a', 'z']))
	print("cht.pop(['a', 'z'])    ", cht.pop(['a', 'z']))
	print("cht.length             ", cht.length )
	nl()
	
	print('Columns changed ', cht.changed )
	print('Rows changed   ', bin(cht.rows_changed()) )
	nl()
	
	print('Child table get_row(3)', cht.get_row(3))
	nl()
	
	
	print('Child table get_rows(5)', cht.get_rows(5))
	nl()
	
	print('Child table get_rows([1,3])', cht.get_rows([1,3]))
	nl()
	
	print('Simpe Index and Query')
	for cname in cht.col_names:
		cht.index_attr(cname)
	nl()
		
	print("(cht.index['col1']['a'] | ( cht.index['col2']['b']) & cht.index['col2']['y'] )")
	bmask = (cht.index['col1']['a'] | cht.index['col1']['b'] ) & cht.index['col2']['y'] 
	print('bmask ', bin(bmask))
	for tp in cht.get_rows(bmask):
		print(tp)
	nl()
	
	
	import sys
	
	if gc_present:

		main_end = mem_free()
		print(f"=== Memory Usage for MicroPython on {sys.platform} ===")
		print('Total memory started: ', mem_start )
		print('Memory use to start of __main___ :', mem_start-main_start)
		print('Mem free at end: ', mem_free())
		print('Total memory used: ', mem_start-main_end)
		collect()
		print('Mem after collect: ',  mem_start-mem_free()) 
		nl()
	
	x = [tstore, tstore2, tdb, tdb2 ]	
	
		
	
	"""

    x = [lstore, lstore2, tdb, tdb2 ]

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
	

