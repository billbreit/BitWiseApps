"""
module:     tablestore
version:    v0.4.1
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

The ListStore and TupleStore base classes also provide lower-level access and indexing. 
	   
 - an indexing store for tuples. Note that indexer can consume 
   large amounts of memory and too memory-intensive for a 256K class platform.
   
 - a cross-platform version of namedlist.py, when Python dataclass is not available.
 
Known to run on Python 3.9, micropython v1.20-22 on a Pico and Arduino Nano ESP32. 
	
"""

try:
	from gc import mem_free, collect
	mem_free_present = True
	mem_start = mem_free()
except:
	mem_free_present = False

import os

import json
from collections import namedtuple, OrderedDict

from liststore import TupleStore

from ulib.fsutils import path_exists, path_separator



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

	_tdef:TableDef = None   # for subclassing

	
	def __init__(self, tdef:TableDef=None, db:'DataStore'=None ):
		""" Based on TupleStore with:
			- uniqueness constraints, assure unique key
			- python types, including namedtuple in columns, recoverable from JSON
			- JSON data store and recovery of non-JSON types, i.e. tuples
			
			- when used in DataStore (db not None), enforce referential integrity,
			  parent/child key rels between tables.

		"""

		if self._tdef is not None:  # use subclass _tdef, will override input
			self.tdef = self._tdef
			# print('_tdef is None ', self._tdef )
		else:
			self.tdef = tdef
			# print('_tdef ', self._tdef )

	
		col_names = [ c.cname for c in self.tdef.col_defs]
		defaults = [ c.default for c in self.tdef.col_defs]

		super().__init__(self.tdef.tname, col_names, defaults)
		
		self.ptypes:list[type] = [ c.ptype for c in self.tdef.col_defs]
		
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
	@classmethod
	def constructor( cls ):
		"""Returns class instance of itself as ttype=class for db constructor.
		   Means that TableSore is subclassed and has cls._tdef."""  
		
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
		
		return [ self.make_key(row) for row in zip(*(self.store))]
		

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
	
		if len(row_in) != len(self.col_names):
			raise TableStoreError(f'Make Key: malformed list {list_in}')
	
		key_vals = [ row_in[self.slot_for_col(k)] for k in self.unique_columns ]

		return key_vals
	
		
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
				errors.append(f"Validation Add Error: key '{key}' is duplicate.")
		else:
			if not self.is_duplicate(key):
				errors.append(f"Validation Update Error: key '{key}' does not exist.") 
		
		# referential integrity 
		err_list = self.validate_parents(row)
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
			raise TableStoreError('Invalid List: list passed can not be None or empty')
			
		err_list = []
		for pt, v in zip(self.ptypes, list_in):
			try:
				self.test_type(pt, v)
			except TableStoreError as e:
				err_list.append(f"Validation Error: value '{v}' must be type {pt}")
				
		return err_list
		
	def fix_types(self, data:list, resolve_namedtuples:bool = False ) -> list:
		"""Restore Python types from JSON.  Resolve namedtuples, that is tuple -> namedtuple."""
	
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
				
		errors = []
		
		# print('in val par ', self.db, self._crelations, self._prelations)
		
		if self.db:
			for ccol, par, pcol in self._crelations:

				pkey = row[self.slot_for_col(ccol)]
				
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
			for pcol, child, ccol in self._prelations:

				ckey = row[self.slot_for_col(pcol)]
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

		
	def get_key(self, key:list ) -> tuple:
		""" Get row with key, return tuple of values."""
		
		if isinstance(key, str): key = [key]
	
		slot = self.find_unique(key)
		
		if slot < 0:
			raise TableStoreError(f"Get Key Error: key '{key}' not found in {self.tablename}.") 
	
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
		
		if col_name in self.unique_columns:  # equivalent to rename (delete/add ) row
			key_changed = True
			ch_list = self.validate_children(rrow)
		
			if len(ch_list) > 0:
				raise TableStoreError(f"Set Error; column {col_name} '{key}' has dependent children. {ch_list}.")
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
		
		# db will re-call table.save providing full 'dir/filename' path
		if self.db and not filename:
			self.db.save_all() 
	
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

"""DBTableDef - Table Definition for DB Table,
	 tname:str,
	 ttype:TableStore or subclass    # added to allow subclassing
	 filename:str,
	 unique:list[str],
	 col_defs:list[ColDef]
"""
DBTDef_fields = ['tname', 'ttype', 'filename',  'unique', 'col_defs']  # no _fields in mpy
DBTableDef = namedtuple('TableDef', DBTDef_fields)

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
	                            # in parent -> child db load order.

	def __init__(self, dbdef:DataStoreDef=None ):
	
		if self._dbdef is not None:
			# rewrite table_defs from class instances to DBTableDef tuples
			
			tdefs = [ tclass.constructor() for tclass in self._dbdef.table_defs ]
			  
			self.dbdef = DataStoreDef( self._dbdef.dbname, self._dbdef.dirname,
			             self._dbdef.relations, tdefs ) 
		else:
			self.dbdef = dbdef

		if len({ tdef.tname for tdef in self.dbdef.table_defs }) != len([ tdef.tname for tdef in self.dbdef.table_defs ]):
			raise DataStoreError('DataStoreDef contains duplicate tables.')
		
		self.tabledict = OrderedDict()  # maintain order, must load top-down
		for tdef in self.dbdef.table_defs:
			self.tabledict[tdef.tname] = tdef.ttype(tdef, self)
		
		for tobject in self.tabledict.values():
			tobject._postinit()  # embeds parent->child and child->parent rels into tables
		
		if not path_exists(self.dbdef.dirname):
			os.mkdir(self.dbdef.dirname)
			
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
			# print('loadall ', fullname)
			tobj.load(fullname)
		
	def save_all(self):
	
		for tname, tobj in self.tables():
			fullname = path_separator().join([self.dirname, tname]) 
			tobj.save(fullname)

def display_table( tstore ):
	# print('Store type  ', type(tstore))
	print('Table name  ', tstore.tablename)
	print('Length      ', tstore.length)
	for attr, col_store in zip(tstore.col_names, tstore.store):
		print('Column ', attr, col_store)
	print()
	print('Index ')
	for k, subdict in tstore.index.items():
		print( k, subdict )
	print()
	print('Columns changed ', [bin(i) for i in tstore.changed])
	print('Rows changed   ', bin(tstore.rows_changed()) )
	print()
	# print('Rows changed indexes ', bit_indexes(lstore.rows_changed()))
	# print('Rows deleted   ', bin(lstore._deleted))            


if __name__ == '__main__':

	nl = print
	
	nl()
	print('=== Test of TableStore/DataStore Classes ===')
	nl()
	
	if mem_free_present:
		collect()   # makes pcio/esp32 more consistent
		main_start = mem_free()


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
	DateTime = namedtuple('DateTime', [ 'year', 'month', 'day', 'hour', 'min', 'secs' ])  # no millis or micros in myp ?
	
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
	
	print("is_duplicate(['MMM', 0] ", tstore.is_duplicate(['MMM', 0]))
	print("is_duplicate(['NNN', 5] ", tstore.is_duplicate(['NNN', 5]))
	
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
	nl()
	for n, t in tdb.tables():
		print('table ', n )
		print('par ', t._prelations)
		print('ch  ', t._crelations)
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
	print('Changed masks ', [t.changed for _, t in tdb.tables()])
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
	
	print('Examining parent and child tables ...')
	nl()
	par2t = tdb2.table('partable2')
	cht = tdb2.table('chtable')
	print("parent table: parents_exist ['a', 'mmm']       ", par2t.parents_exist([ 'a', 'mmm', 'testing a.z']), ' -> problem, has no parents, so has required parents is True')
	print("parent table: children_exist ['x', 'mmm']      ", par2t.children_exist([ 'x', 'mmm', 'testing a.z']))
	print("parent table: val children ['y', 'mmm']        ", par2t.validate_children([ 'y', 'mmm', 'testing a.z']))
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

	print('THE END ... ALMOST ')
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
	
	x = [tstore, tstore2, tdb, tdb2 ]   # hold reference for collect()  
	
		
	
	for db in [ tdb, tdb2 ]:
		db.clear_all()
		print('DB name ', db.dbname , ' is cleared.')
		for name, tbl in db.tables():
			print('Table ', name , ' cleared.  Len is ', tbl.length)
		nl()
		
	print('=== SubClassing ===')
	nl()
	
	
	class MyTable(TableStore):
	
		_tdef = TableDef(tname = 'MyTable', filename = 'mytable111', unique=['col1'],
					 col_defs = [ColDef(cname='col1', default=None, ptype=str),
								 ColDef(cname='col2', default=0, ptype=int),
								 ColDef(cname='col3', default=0.0, ptype=float),
								 ColDef(cname='col4', default={}, ptype=dict)])
								 
		def sum(self, col_name ):
			
			return sum(self.get_column(col_name))

								 
	mt = MyTable()
	print('mt tdef ', mt.tdef)
	nl()
	print('dir(mt) ', dir(mt))
	nl()
	
	mt.extend([[ 'a', 123, 7.3, {'hello':1, 'world':2}],
	           [ 'b', 12423, 33.5, {'goodbye':999, 'world':777}],
	           [ 'c', 523, 21.66, {'helloagain':999, 'yall':777}]])
	
	for attr in mt.col_names:
		mt.index_attr(attr)
	           
	display_table(mt)
	print()
	
	print('sum of col2: ', mt.sum('col2')) 
	print('sum of col3: ', mt.sum('col3')) 
	nl()

	print('isinstance(mt, MyTable) ', isinstance(mt, MyTable))
	print('isinstance(mt, TableStore) ', isinstance(mt, TableStore))
	print('isinstance(mt, TupleStore) ', isinstance(mt, TupleStore))
				
	nl()
	

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
	

