"""
liststore - a column-oriented data store with:
- a generalized structure for csv style lists
 - an indexing store for tuples
 - a cross-platform version of namedlist.py, when Python dataclass is not available.
 
Known to run on Python 3.9, micropython v1.20-22 on a Pico and Arduino Nano ESP32. 

module:     liststore
version:    v0.3.2
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2023 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer
    
"""

try:
    from gc import mem_free, collect
    gc_present = True
except:
    gc_present = False
    
if gc_present:
    mem_start = mem_free()
    

from collections import namedtuple

# from datetime import datetime
# import time

from math import log, floor, ceil

from ulib.getset import itemgetter
from ulib.bitops import power2, bit_indexes


nl = print

""" mpy 
>>> dir(list)
['__class__', '__name__', 'append', 'clear', 'copy', 'count', 'extend', 'index',
'insert', 'pop', 'remove', 'reverse', 'sort', '__bases__', '__dict__']


"""



class ListStoreBaseError(Exception):
	pass
		

class ListStoreBase(object):
	""" Constructor class for ListStore. Basic features and a few utility methods."""

		
	def __new__(cls, column_defs:list=None, defaults:list=None, types:list=None, *args, **kwargs):
	
		# print('In new ', column_defs, defaults, types ) 
		
		if column_defs is None or not isinstance(column_defs, list) or column_defs==[]:
			raise ListStoreBaseError('ListStore column_def must have at least one column, in form List[str].')
		
		nclass = super().__new__( cls )
		
		nclass.__slots__ = column_defs
		nclass._defaults = defaults or []
		nclass._types = types or []
		nclass._store = []
			
		for i in range(len(nclass.__slots__)):
			nclass._store.append([])

		for i, sl in enumerate(nclass.__slots__):
			iget = itemgetter(i)(nclass._store)  # getter only, no setter
			setattr(nclass, sl, iget)
	  
		return nclass
		
	
	def __init__(self, *args, **kwargs ):
			
		super().__init__()   # *args, **kwargs dropped ?  May help in long run.
	
	
	@property
	def length(self):
		return len(self._store[0])
	
	@property
	def slots(self):
		return self.__slots__
	
	@property
	def defaults(self):
		return self._defaults
	
	@property
	def types(self):
		return self._types
	
	@property
	def store(self):
		return self._store
		
		
		
class ListStoreError(Exception):
			pass

				
class ListStore(ListStoreBase):
	"""List-like storage for lists and tuples, impemented with
	   columns rather than rows.
	   
	   column_defs List[str]  name strings for now, maybe a list of ColDef tuples.
	   defaults    List[Any], applied from right to left, last default to last column
	   types       List[Any]  applied from left to right, first type to first column
		"""
		
	def __init__(self, column_defs:list=None, defaults:list=None, types:list=None, *args, **kwargs ):

		if column_defs is None or column_defs==[]:
			raise ListStoreError('ListStore column_def must have at least one column, in form List[str].')
			
		super().__init__( column_defs, defaults, types, *args, **kwargs)
		
		self._changed = [ 0 for i in range(len(self.slots))]  # list[int] for each column
		self._deleted = 0     # not used yet, a single int mapping rows in changed columns
		self._indexer = Indexer(self.slots, self.store )
		
		
	@property
	def indexer(self):
		return self._indexer

	@property
	def index(self) -> dict:
		return self._indexer.index
		
	@property
	def changed(self) -> int:
		return self._changed
		
	def rows_changed(self) -> int:
		"""Return column mask of rows changed, by ORing in each
		   column changed mask yielding rows changed."""
	
		rc = 0
		for i in range(len(self.slots)):
			rc |= self._changed[i]
		
		return rc
		
	def values_changed(self, row:int) -> int:
		"""Row mask for values changed in a given row, probably working
		   back from the return of rows_changed()."""
		   
		col_c = 0
		for i in range(len(self.slots)):
			col_c |= power2(row) & self._changed[i]
		
		return col_c

	def reset_changed_row(self, slot:int):
		"""Implies single reader, may need reset_changed_slot for multiple readers"""
		for i in range(len(self.slots)):
			self._changed[i] &= ~power2(slot)
			
		
	def reset_changed(self):
		"""Implies single reader, may need reset_changed_slot for multiple readers"""
		for i in range(len(self.slots)):
			self._changed[i] = 0
	
	def resolve_defaults(self, in_list:list) -> list:
	
		ilist = list(in_list)
		
		if len(self.defaults)+len(ilist) >= len(self.slots):
		
			defs_needed = len(self.slots)-len(ilist)
			dlist = self.defaults[-defs_needed:]
			
			for d in dlist: 
				ilist.append(d)
		else:
			raise ListStoreError('Not enough defaults to fill missing values.')
			
		return ilist
		
	def check_slot(self, slot:int):
	
		if slot < 0:
			raise ListStoreError('Slot number must greater than 0.')
		
		if slot > len(self.store[0]):
			raise ListStoreError('Slot number given is greater than length of ListStore.')
		
	def slot_for_col(self, col_name:str) -> int:
		"""slot number for column name""" 
		
		return self.slots.index(col_name)
		
	def get(self, col_name:str, slot:int):
		"""Get single slot from a column."""
	
		self.check_slot(slot)
		
		return self.store[self.slot_for_col(col_name)][slot]
		
	def get_row(self, slot:int) -> list:
		"""Get a row, across all columns."""
	
		self.check_slot(slot)
			
		return [ self.store[i][slot] for i in range(len(self.slots)) ]
		
	def get_rows(self, mask:int ) -> list:
		""" make rows from access mask """
		
		if mask == 0: return []
		# print('mask ', mask)
		
		rows = [ self.get_row(i) for i in bit_indexes(mask) ]
				
		return  rows
		
	def set(self, col_name:str, slot:int, value ):
		"""Set col_name (attr) in slot int to value"""
		
		self.check_slot(slot)
		
		col_slot = self.slot_for_col(col_name)
		
		old_value = self.store[col_slot][slot]
		
		self.store[col_slot][slot] = value
		
		self.indexer.update_index( col_name, slot, old_value, value)
		
		self._changed[col_slot] |= power2(slot) 

			
	def append( self, in_list:list=None ):
		"""Append to list and update index with append_index.
		   No need to index_attr entire column, all bitmasks
		   will stll be valid. """
	
		if in_list is None:
			raise ListStoreError('Append - list passed can not be None')  
			
		# defaults  
		if len(in_list) != len(self.store):
			if self.defaults:
			
				in_list = self.resolve_defaults(in_list)
				
			else:
				raise ListStoreError('List missing values and no defaults defined.')
				
		ilist = list(in_list)

		for i, v in enumerate(ilist):
			self.store[i].append(v)
		
		if self.indexer.index:
			self.indexer.append_index(ilist)
			
		for i in range(len(ilist)):
			self._changed[i] |= power2(len(self.store[0])-1)
			
	def extend(self, list_of_lists:list=None):
	
		if list_of_lists is None:
			raise ListStoreError('No input list provided.')
		
		for lst in list_of_lists:
			self.append( lst )
			
	def pop(self, row:int ):
		""" Remove slots in liststore for a given row, and reindex from scratch
			to guarantee bitmask references, probably very slow, maybe several
			hundred milliseconds (?) """
		
		popped_row = []	
		self.check_slot(row)
			 
		for i in range(len(self.slots)):
			popped_row.append(self.store[i].pop(row))
			
		self.indexer.reindex()
		
		return popped_row
				
	def dump(self) -> list[list]:
		"""Dump all rows as List[List] """
		return [ list(lst) for lst in zip(*list(self._store))]

			
	def index_attr(self, attr_name:str):
		"""Create new index for attr.column name"""
		
		self._indexer.index_attr(attr_name)
		
	def update_index(self, n_list:list):
		"""Update index with new list for row, or tuple """
	
		self._indexer.update_index(n_list)
		
	def reindex(self):
		""" Rebuild entire index,. slow """
		self._indexer.reindex()
		



class TupleStoreError(Exception):
			pass
				
class TupleStore(ListStore):
	"""List-like storage for tuples, impemented with
	   columns rather than rows.  Updatable without new instance.
		"""
		
	def __init__(self, nt_name:str, column_defs:list=None, defaults:list=None, types:list=None, *args, **kwargs ):
	
		# print('in TS init ', args, kwargs )
			
		super().__init__( column_defs, defaults, types, *args, **kwargs)
		

		self._ntuple = namedtuple( nt_name, self.slots)

	
	@property	
	def ntuple(self) -> tuple:
		return self._ntuple
		
	def get_row(self, slot:int) -> tuple:
		row = super().get_row(slot)
		return self._ntuple(*row)
		
		
	def pop(self, slot:int ) -> tuple:
		""" pop slot number """
		
		popped_list = super().pop(slot)
		return self._ntuple(*popped_list)
			
	def make_tuple(self, slot ) -> tuple:
	
		val_tuple = [self._store[i][slot] for i in range(len(self.slots))]
			
		return  self._ntuple(*tuple(val_tuple))
		
	def make_tuples(self, mask:int ) -> list[tuple]:
		""" make tuples from access mask """
	
		n_tuples = []
		
		if mask == 0: return n_tuples
		
		n_tuples = [self.make_tuple(i) for i in range(len(self.store[0])) if mask & power2(i) >= 1 ] 
						
		return  n_tuples
		
	def dump(self):
		return [ self._ntuple(*tup) for tup in zip(*tuple(self._store))]
		


class IndexerError(Exception):
	pass

class Indexer(object):

	def __init__(self, slots:list=None, store:list=None, usertypes=None, *args, **kwargs ):
	
		super().__init__( *args, **kwargs)
		
		if slots == None or len(slots) == 0:
			raise IndexerError('A list of column keys must provided to Indexer.') 
		
		self._slots = slots
		self._store = store or []  # empty liststore means class methods only       
		self._index = {}
		self._indexed = []  # list of columns actually indexed, using index_attr()
		
		self._indexable = [ str, int, tuple, type(None) ]
		
		if usertypes:
			self._indexable.extend( usertypes )
			
		self._indexable = tuple(self._indexable)
		
	@classmethod
	def index_list(cls, alist:list ) -> dict:
		"""index values in a list or tuple"""
		
		col_value_set = set()
		for value in alist:
			if type(value) in cls._indexable:
				col_value_set.add(value)
	
		""" init subdict """
		sub_dict = dict()
		for value in col_value_set:
			sub_dict[value] = 0
		
		""" iterate through a column of store and add/update int bit mask
		    values in subdict """	
		    
		for i, value in enumerate(alist):
			if type(value) in cls._indexable:
				if value in col_value_set:
					sub_dict[value] |= power2(i)
	
		return sub_dict
		
		
	
	@property	
	def index( self):
		"""return ref to internal index."""
		return self._index
			
		
	def index_attr(self, attr_name):
		"""Create new index for attr.column name"""
	
		if attr_name not in self._slots:
			raise IndexerError('Index Attr -  Columns name ', attr_name, ' not known.')
	
		storage_slot = self._slots.index(attr_name)
		
		""" build set of unique values, if indexable type """
		col_value_set = set()
		for value in self._store[storage_slot]:
			if type(value) in self._indexable:
				col_value_set.add(value)
	
		""" init subdict """
		sub_dict = dict()
		for value in col_value_set:
			sub_dict[value] = 0
		
		""" iterate through a column of store and add/update int bit mask
		    values in subdict """	
		    
		for i, value in enumerate(self._store[storage_slot]):
			if type(value) in self._indexable:
				if value in col_value_set:
					sub_dict[value] |= power2(i)
	
		self._index[attr_name] = sub_dict
		if attr_name not in self._indexed: self._indexed.append(attr_name)

		
	def update_index(self, attr_name, row_slot, old_value, new_value):
		"""An altered row via set().  Need to unset bit on old value and
		   set bit for new value."""
	
		if attr_name not in self._indexed: return
		
		self.index[attr_name][old_value] &= ~power2(row_slot)
		
		if self.index[attr_name][old_value] == 0:
			del self.index[attr_name][old_value]

		if type(new_value) in self._indexable:
		
			if new_value not in self.index[attr_name].keys():
				self.index[attr_name][new_value] = 0
			
			self.index[attr_name][new_value] |= power2(row_slot)		
		
			
	def append_index(self, n_tuple):
		"""New slot value, for appended row. No need to rebuild masks, just OR in new offset."""
	
		for col_name in self._index.keys():
		 
			store_slot = self._slots.index(col_name)
			new_slot = len(self._store[store_slot])   # current new slot
				
			if n_tuple[store_slot] not in self._index[col_name]:
				self._index[col_name][n_tuple[store_slot]] = 0

			self._index[col_name][n_tuple[store_slot]] |= power2(new_slot) 
		
	def reindex( self):
		"""build or rebuild index completely, after row pop/remove."""

		for attr_name in self._indexed:
			self.index_attr(attr_name)
		
	def query(self, col_name:str, indexed_value ):
		""" -> Query( col_name, indexed_value, bitint """
		pass
	


				
if __name__ == '__main__':
				
	print('Test Script for ListStore/TupleStore ')
	nl()
	
	if gc_present:
		main_start = mem_free()
		
	def display_store( lstore ):
		print('lstore.store ')
		print('lstore.length ', lstore.length)
		nl()
		for attr, col_store in zip(lstore.slots, lstore.store):
			print('Column ', attr, col_store)
		nl()
		print('lstore.index ')
		nl()
		for k, subdict in lstore.index.items():
			print( k, subdict )
		nl()
		print('lstore._changed ', lstore._changed )
		print('lstore.rows_changed() ', bin(lstore.rows_changed()) )
	
	try:
		la = ListStore('BadTest')
	except Exception as e:
		print('Exception: ', e)
		nl()
	else:
		print('ERROR: Should be Exception - woops.')
		nl()
		
	print("Create ListStore(['name','address', 'phone', 'email', 'num_of_RPZeros']")
	nl()
		
	ls = ListStore(['name','address', 'phone', 'email', 'num_of_RPZeros'])
	
	ls_data = [[ 'Bill', '22 AnyWhere', '999-888-7777', 'billb@xxx.net', 17],
			   [ 'Bob K.', '44 AnyWhere But Here', '222-333-4447', 'bobk@yyy.net', 4],
			   [ 'Sally', '22 AnyWhere', '999-888-7777', 'sally@xxx.net', 0],   
			   [ 'Sam', '66 EveryWhere', '888-444-44447', 'samy@yyy.net', 1], 	 
			   [ 'Mary', '88 NoWhere', '888-444-0000', 'mary@zzz.net', 18]]
			   
	for ll in ls_data:
		ls.append(ll)
		
	ls.reindex()
	
	display_store(ls)
	nl()
	
	print('ls.reset_changed()')
	nl()
	ls.reset_changed()
	
	print('Index address and num_of_RPZeros')
	ls.index_attr('address')
	ls.index_attr('num_of_RPZeros')
	nl()
	
	print("ls.get('name', 2)")
	print(ls.get('name', 2))
	nl()
	
	print("ls.set('address', 4, '367 SomeWhere')")
	ls.set('address', 4, '367 SomeWhere')
	nl()
	
	print("ls.set('num_of_RPZeros', 2, 27)")
	ls.set('num_of_RPZeros', 2, 27)
	nl()

	display_store(ls)
	nl()
	
	nl()
	print('ls.get_rows(ls.rows_changed()) ', ls.get_rows(ls.rows_changed()))
	nl()
	 
	
	print('try to trigger no defaults error')
	try:
		ls.append(['error','no defaults'])
	except Exception as e:
		print(e)
	else:
		print('ERROR: Shoud be an error for no defaults')
	nl()
	
	print('Dump ListStore ... ')
	nl()
	for ll in ls.dump():
		print(ll)
	nl()
	
	if gc_present:
		mem_lstore = mem_free()	
	
	
	#############################	
	print('=== TupleStore ===')
	nl()
	

	print("ts = TupleStore(nt_name = 'Testing',")
	print("                column_defs= [ 'aaa', 'bbb', 'ccc', 'ddd' ],")
	print("          	   defaults= [ 'default3', 'default4'])")
	nl()

	ts = TupleStore(nt_name = 'Testing',
					column_defs= [ 'aaa', 'bbb', 'ccc', 'ddd' ],
					defaults= [ 'default3', 'default4'])
	nl()

	# print('dir(ts) ', dir(ts))
	nl()
	display_store(ts)
	nl()
	


	myTest = ts.ntuple
	print('ts.ntuple', myTest)
	nl()
	
	myTest = ts.ntuple
	tsnt = myTest('test66', 'always', 'rule-based', 999 )
	print('myTest instance ', tsnt )
	print('type            ', type(tsnt))
	nl()

	print("append(Testing(aaa='test66', bbb='always', ccc='rule-based', ddd=999))")	
	ts.append(tsnt)
	nl()

	
	print("append(('test1', 'always'))")
	ts.append(('test1', 'always' ))
	nl()
	
	display_store(ts)
	nl()
	
	print("ts.reset_changed()")
	ts.reset_changed()
	nl()
	
	print("append(('test2','often', 'loot-based', 24 ))")   
	ts.append(('test2','often', 'loot-based', 24 ))
	
	print("append(('test2', 'sometimes', 'values_based' )")
	ts.append(('test2', 'sometimes', 'values_based' ))
	nl()
	print("ts.index_atttr('aaa')")
	ts.index_attr('aaa')
	nl()

	display_store(ts)
	nl()
	
	print('ts.reset_changed()')
	nl()
	ts.reset_changed()

	
	nt = ts._ntuple( ts.aaa[0], ts.bbb[0], ts.ccc[0], ts.ddd[0]) 
	print('From _ntuple', nt)
	nl()

	"""
	for i in range(len(ts.store[0])):
		print('slot ', i, ts._ntuple( ts.aaa[i], ts.bbb[i],  ts.ccc[i], ts.ddd[i] ))
		nl()
	"""
		
		
	tups = [('tesxx','often', 'loot-based', None ),
			('test2','never', 'loot-based', [ 1, 2, 3 ]),
			('test2','occasionally', 'food-based', 44 ),
			('test2','often', 'luck-based', 24 ),			
			('tesxx','often', 'loot-based', ( 3, 4, 5)),
			('test2','never', 'bot-based', None ),
			('tesxx','often', 'loot-based', 24 ),
			('test2','often', 'loot-based', ( 3, 4, 5 ))]
			
	print('Appending 8 rows ...')
	nl()
			
	for tup in tups:
		ts.append(tup)
	nl()
	print('Done appending.')
	nl()
	
	nl()    
	display_store(ts)
	nl()
	
	print('ts.reset_changed()')
	nl()
	ts.reset_changed()	
	
	print('Pop/remove row 3.  Note: requires reindexing, very slow, use discouraged !') 
	popped = ts.pop(3)
	print('popped tuple ', popped)
	nl()
	
	display_store(ts)
	nl()
	print('Note that pop does not set changed bit for row, no slot to refer to.')
	nl()
	print('May need to implement deleted int for row so can do queries like ')
	print('ls.changed & ~ls.deleted to retain changed info for row, and allow ')
	print('adjustment of the index for the popped row rather than reindexing entirely.')  
	nl()
	
	print('Making tuples, using attrs, like ts.aaa[0], ts.bbb[0] .. etc.')
	nl()
	for i in range(len(ts.store[0])):
		print('slot ', i, ts.ntuple( ts.aaa[i], ts.bbb[i],  ts.ccc[i], ts.ddd[i] ))
	nl()

	
	############################
	print('=== Indexing ===')
	nl()
	
	for at in ts.slots:
		print('=  Indexing Attr', at, '  =')
		nl()
		ts.index_attr(at)
	nl()
	
	print("ts.index['aaa'] ", ts.index['aaa'])
	nl()

	for k, v in ts.index['aaa'].items():
		print( k, bin(v))
	nl()
	
	nt = ts._ntuple( 'aaa', 3434,  888, 23.7 )
	
	print('append ts._ntuple ', nt )
	nl()
	
	ts.append(nt)
	nl()
	
	print('Index all columns - reindex()')
	ts.reindex()

	display_store(ts)
	
	print('Skipping index tests ...')
	
	'''
	
	print("for key in ['aaa']: use bitmasks to build lists of tuples.")
	nl()
	for key in ['aaa']:
		print('Index ', key )
		for value in ts.index[key].keys():
			print( 'value: ', value, '      mask: ', bin(ts.index[key][value]))
			ntuples = ts.make_tuples(ts.index[key][value])
			for n in ntuples:
				print(n)
			nl()
		nl()
	nl()

	
	print('for k, v in index.items():')
	for key, vals in ts.index.items():
		print('Index for attr ', key )
		nl()
		print(vals)
		nl()
		for k, v in vals.items():
			print( k, type(k),  bin(v))
		nl()
	'''		
	
	print('Dump ...')
	nl()	
	for nt in ts.dump():
		print(nt)
	nl()
	
	print('=== ListStore Queries  ===')
	nl()
	
	print("ts.make_tuples(ts.index[ccc'][888]")
	print(ts.make_tuples(ts.index['ccc'][888]))
	nl()
	
	
	# print( len(ts.a), len(ts.b), len(ts.c), len(ts.d))
	
	print("ts.index['aaa']['test1'] ", ts.index['aaa']['test1'])
	print("ts.index['bbb']['always'] ", ts.index['bbb']['always'])
	nl()
	print("ts.index['aaa']['test1'] & ts.index['bbb']['always']")
	bmask = ts.index['aaa']['test1'] & ts.index['bbb']['always']
	print('bmask ', bin(bmask))
	print(ts.make_tuples(bmask))
	nl()
	
	print("ts.index['aaa']['test1'] | ( ts.index['aaa']['tesxx'] & ts.index['ddd'][None] )")
	bmask = ts.index['aaa']['test1'] | ( ts.index['aaa']['tesxx'] & ts.index['ddd'][None] )
	print('bmask ', bin(bmask))
	for tp in ts.make_tuples(bmask):
		print(tp)
	nl()
	
	print("ts.index['aaa']['tesxx'] & ~ts.index['ddd'][None]")
	bmask = ts.index['aaa']['tesxx'] & ~ts.index['ddd'][None]
	print('bmask ', bin(bmask))
	for tp in ts.make_tuples(bmask):
		print(tp)
	nl()
	print('End of Test')
	nl()
	
	if gc_present:
		main_end = mem_free()
		print('=== Memory Usage for MicroPython ===') 
		print('Total memory started ', mem_start )
		print('Memory use to start of __main___ ', mem_start-main_start)
		print('ListStore with instance ', main_start - mem_lstore )  
		print('Total memory used ', mem_start-main_end)
		collect()
		print('Mem after collect ',  mem_start-mem_free()) 
		nl()
	
