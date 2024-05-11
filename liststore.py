"""
module:     liststore
version:    v0.4.1
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

liststore - a column-oriented data store using a generalized list of lists structure, 
with typical list-like operations. For *small datasets*, maybe a few hundred rows,
especially on limited memory micro-controllers.
           
 - an indexing store for tuples. Note that indexer can consume 
   large amounts of memory and too memory-intensive for a 256K class platform.
   
 - a cross-platform version of namedlist.py, when Python dataclass is not available.

For example, a structure for column_defs ['name', 'address', 'phone']:

people = [[ 'Bob', '733 Main Street', '123-456-7890' ],
          [ 'Mary', '22 Any Avenue', '123-456-2222' ],
          [ 'Sue', '11 My Way', '123-456-3333' ]]
          
ls = ListStore(['name', 'address', 'phone'])
          
ls.extend(people)

ls._store = [['Bob', 'Mary', 'Sue'],
             ['733 Main Street', '22 Any Avenue', '11 My Way'],
             ['123-456-7890', '222-444-6666', '123-456-7890' ]]
             
ls.get(1, 'address' ) would return '22 Any Avenue'
ls.set(0, 'address', '999 Any Avenue' ) would set Bob's address.
        
ls.get_row( 0 ) would return ['Bob', '999 Any Avenue', '123-456-7890']

Known to run on Python 3.9, micropython v1.20-22 on a Pico and Arduino Nano ESP32. 

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

# from ulib.getset import itemgetter
from ulib.bitops import power2, bit_indexes, bitslice_insert, bit_remove


nl = print

""" mpy 
>>> dir(list)
['__class__', '__name__', 'append', 'clear', 'copy', 'count', 'extend', 'index',
'insert', 'pop', 'remove', 'reverse', 'sort', '__bases__', '__dict__']


"""

		
		
class ListStoreError(Exception):
			pass

				
class ListStore(object):
	"""List-like storage for lists and tuples, impemented with
	   columns rather than rows.
	   
	   column_defs List[str]  name strings for now, maybe a list of ColDef tuples.
	   defaults    List[Any], applied from right to left, last default to last column
	   types       List[Any]  applied from left to right, first type to first column
		"""
		
	def __init__(self, column_names:list=None, defaults:list=None, *args, **kwargs ):

		if column_names is None or not isinstance(column_names, list) or column_names==[]:
			raise ListStoreError('ListStore column_def must have at least one column, in form List[str].')
			
		super().__init__()
		
		self.col_names = column_names
		self.defaults = defaults or []
		
		self.store = []
			
		for i in range(len(self.col_names)):
			self.store.append([])
		
		self.changed = [ 0 for i in range(len(self.col_names))]  # list[int] for each column
		self.indexer = Indexer(self.col_names, self.store )
		
	def __iter__(self) -> list[list]:
		"""Yeild columns as list of lists, an iterator over rows."""

		yield from [ list(row) for i, row in enumerate(zip(*(self.store))) ]
		
	@property
	def length(self) -> int:
		return len(self.store[0])
	
		
	def rows_changed(self) -> int:
		"""Return column mask of rows changed, by ORing in each
		   column changed mask yielding rows changed."""
	
		rc = 0
		for i in range(len(self.col_names)):
			rc |= self.changed[i]
		
		return rc
		
	def values_changed(self, row:int) -> int:
		"""Column indexes for values changed in a given row, probably working
		   back from the return of rows_changed(). The values are then 
		   store[col][row1...col_len]"""
		   
		column_indexes = [ i for i in range(len(self.col_names)) if power2(row) & self.changed[i]]
		
		return column_indexes

		
	def reset_changed(self, slot:int=None):
		"""Reset changed mask for row slot or if slot is None, reset changed for all columns. """
		
		if slot: self.check_slot(slot)
		
		for i in range(len(self.col_names)):
			if slot is not None:
				self.changed[i] &= ~power2(slot)			
			else:
				self.changed[i] = 0
	
	def resolve_defaults(self, in_list:list) -> list:
	
		if len(in_list) == 0 or len(in_list) > len(self.col_names):
			raise ListStoreError('Input length must greater than zero and less than/equal to len(col_names).')
			
		if len(in_list) == len(self.col_names):
				return in_list
	
		ilist = list(in_list)
		
		if len(self.defaults)+len(ilist) >= len(self.col_names):

			defs_needed = len(self.col_names)-len(ilist)
			dlist = self.defaults[-defs_needed:]
			
			for d in dlist: 
				ilist.append(d)
		else:
			raise ListStoreError('Not enough defaults to fill missing values.')
			
		return ilist
		
	def check_slot(self, slot:int):
	
		if slot < 0:
			raise ListStoreError(f'Slot number {slot} must greater than 0.')
		
		if slot > len(self.store[0]):
			raise ListStoreError(f'Slot number {slot} is greater than length of ListStore.')
		
	def slot_for_col(self, col_name:str) -> int:
		"""slot number for column name"""
		
		try:
			index = self.col_names.index(col_name)
		except:
			return -1
		
		return index
		
	def get(self, slot:int, col_name:str):
		"""Get single slot from a column."""
	
		self.check_slot(slot)
		
		return self.get_column(col_name)[slot]
		
	def get_column(self, col_name:str ) -> list:
		"""Return a list of values for 'col_name'. """
	
		return self.store[self.slot_for_col(col_name)]
		
		
	def get_row(self, slot:int) -> list:
		"""Get a row, across all columns."""
	
		self.check_slot(slot)

		return [ self.store[i][slot] for i in range(len(self.col_names)) ]
		
	def get_rows(self, int_or_list ) -> list[list]:
		""" make rows from access mask,
			if int_or_list is type int, make list of bitindexes"""
		
		if isinstance(int_or_list, int):
			if int_or_list == 0:
				return []
				
			else:
				int_list = bit_indexes(int_or_list)
		else:
			int_list = int_or_list
			
		return [ self.get_row(i) for i in int_list ]
		
	def set(self, slot:int, col_name:str, value ):
		"""Set col_name (attr) in slot int to value"""
		
		self.check_slot(slot)
		
		col_slot = self.slot_for_col(col_name)

		old_value = self.store[col_slot][slot]
		
		self.store[col_slot][slot] = value
		
		self.indexer.update_index( col_name, slot, old_value, value)
		
		self.changed[col_slot] |= power2(slot) 

			
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
			
		for i in range(len(ilist)):
			self.changed[i] |= power2(len(self.store[0])-1)
				
		if self.indexer.index:
			self.indexer.append_index(ilist)
			
	def extend(self, list_of_lists:list=None):
	
		if list_of_lists is None:
			raise ListStoreError('No input list provided.')
			
		#resolve defaults
		errs = []
		new_list = []
		
		for lst in list_of_lists:
			if len(lst) != len(self.store):
				if self.defaults:
					try:
						ld = self.resolve_defaults(lst)
					except Exception as e:
						errs.append(e)
					else:
						new_list.append(ld)
						
				else:
					raise ListStoreError('List missing values and no defaults defined.')
			else:
				new_list.append(lst)
			
		if len(errs) > 0:
			raise ListStoreError('Extend Erros: Not enough values or defaults', e )
			
		save_top = self.length  # top_bit, that is last bit + 1
			
		# transpose list of rows to list of columns
		col_list = [ l for l in zip(*new_list)] 

		for i, column in enumerate(self.store):
			self.store[i].extend( col_list[i] )
			
		for i in range(len(self.store)):
			# insert to the right of last bit index + 1 
			self.changed[i] = bitslice_insert( self.changed[i],
												save_top, 
												len(list_of_lists),
												(1 << ( len(list_of_lists)))-1 )
						
		if self.indexer.index:
			self.indexer.extend_index(list_of_lists)

			
	def pop(self, row:int ) -> list:
		""" Remove slots in liststore for a given row, and reindex from scratch
			to guarantee bitmask references, probably very slow, maybe several
			hundred milliseconds (?) """
		
		popped_row = [] 
		self.check_slot(row)
			 
		for i in range(len(self.col_names)):
			popped_row.append(self.store[i].pop(row))

		for i in range(len(self.col_names)):
			self.changed[i] = bit_remove(self.changed[i], row)
			
		# self.indexer.reindex()
		self.indexer.pop_index(row)  # may be faster ?
		
		return popped_row
		
	def clear(self):
	
		if len(self.col_names) == 0: return
		
		for i in range(len(self.col_names)):
			self.store[i] = []
		
		self.reset_changed()	
		self.indexer = Indexer(self.col_names, self.store )
			
		return
				
	def dump(self) -> list[list]:
		"""Dump all rows as List[List] """
		return [ list(row) for row in zip(*(self.store))]
		
		
	def find( self, col_name:str, value, start=0 ) -> int:
		"""Return the first row number for match value in column. """

		try:
			i = self.get_column(col_name).index(value, start)
		except ValueError as ve:
			i = -1
	
		return i

	def find_all ( self, col_name:str, value ) -> list[int]:
		"""Return list of slot numbers for all match values in column. """ 

		slot_index = self.slot_for_col(col_name)
		il = []
		start = 0
		i = 0

		while i > -1:
			try:
				i = self.store[slot_index].index(value, start)
				il.append(i)
				start = i + 1
			except ValueError as ve:
				i = -1

		return il
		
	""" Index Methods """
	


	@property
	def index(self) -> dict:
		return self.indexer.index

	def index_attr(self, attr_name:str):
		"""Create new index for attr.column name"""
		
		self.indexer.index_attr(attr_name)
		
	def reindex(self):
		""" Rebuild entire index, may be slow for large store """
		self.indexer.reindex()
		



class TupleStoreError(Exception):
			pass
				
class TupleStore(ListStore):
	"""List-like storage for tuples, impemented with
	   columns rather than rows.  Updatable without new instance.
		"""
		
	def __init__(self, nt_name:str, column_defs:list=None, defaults:list=None, *args, **kwargs ):
			
		super().__init__( column_defs, defaults, *args, **kwargs)
		
		self.nt_name = nt_name
		self.ntuple_factory = namedtuple( nt_name, self.col_names)
		
	def __iter__(self) -> list[tuple]:
		"""Yeild columns as list of lists, an iterator over rows."""
		
		yield from [ self.ntuple_factory(*row) for row in zip(*(self.store))]
		
		
	def make_namedtuple( self, tup_values:list ) -> tuple:
		"""Make tuple with defaults according to spec., then return, no update."""

		tp = self.resolve_defaults(tup_values)
		return self.ntuple_factory(*tp)
		
	def get_row(self, slot:int) -> tuple:
		""" Get row using slot, return namedtuple. """
		row = super().get_row(slot)
		return self.ntuple_factory(*row)
		
	def get_rows(self, int_or_list ) -> list:
	
		return [self.ntuple_factory(*r) for r in super().get_rows(int_or_list)]
		
	def pop(self, slot:int ) -> tuple:
		""" pop slot number """
		
		popped_list = super().pop(slot)
		return self.ntuple_factory(*popped_list)

		
	def dump(self) -> list[tuple]:
		return [ self.ntuple_factory(*tup) for tup in zip(*tuple(self.store))]
		


class IndexerError(Exception):
	pass

class Indexer(object):

	_indexable = [ str, int, tuple, type(None) ]

	def __init__(self, col_names:list=None, store:list=None, usertypes=None, *args, **kwargs ):
	
		super().__init__( *args, **kwargs)
		
		if col_names == None or len(col_names) == 0:
			raise IndexerError('A list of column keys must provided to Indexer.') 
		
		self._slots:list[str] = col_names
		self._store = store or []  # empty liststore means class methods only       
		self._index:dict = {}
		self._indexed = []  # list of columns actually indexed, using index_attr()
		
		if usertypes:
			self._indexable.extend( usertypes )
			
		self._indexable = tuple(self._indexable)
		
	@classmethod
	def index_list(cls, alist:list ) -> dict:
		"""index values in a list or tuple"""
		
		col_value_set = set()  # unique indexable dict keys
		for value in alist:
			if type(value) in cls._indexable:
				col_value_set.add(value)
	
		""" init subdict """
		sub_dict = dict()
		for value in col_value_set:
			sub_dict[value] = 0
		
		""" iterate through alist and add/update int bit mask
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
			
		
	def index_attr(self, attr_name:str):
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

		
	def update_index(self, attr_name:str, row_slot:int, old_value, new_value):
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
		
			
	def append_index(self, list_in:list):
		"""New slot value, for appended row. No need to rebuild masks, just OR in new offset."""
	
		for col_name in self._index.keys():
		 
			store_slot = self._slots.index(col_name)
			new_slot = len(self._store[store_slot])   # current new slot
				
			if list_in[store_slot] not in self._index[col_name]:
				self._index[col_name][list_in[store_slot]] = 0

			self._index[col_name][list_in[store_slot]] |= power2(new_slot) 
			
	def extend_index(self, list_of_lists:list[list]):
	
		for l in list_of_lists:
			self.append_index( l )
			
	def pop_index(self, row_slot:int ):
		"""Delete one bit from masks in subdict for attr name. """
		
		for attr_name in self._indexed:
			for key, value in self.index[attr_name].items():
				self.index[attr_name][key] = bit_remove(self.index[attr_name][key], row_slot)
		
	def reindex( self):
		"""build or rebuild index completely, after row pop/remove."""

		for attr_name in self._indexed:
			self.index_attr(attr_name)
		
	def query(self, col_name:str, indexed_value ):
		""" -> Query( col_name, indexed_value, bitint """
		pass
	

def display_store( lstore ):
	print('Store type  ', type(lstore))
	print('Length      ', lstore.length)
	# nl()
	for attr, col_store in zip(lstore.col_names, lstore.store):
		print('Column ', attr, col_store)
	nl()
	print('Index ')
	for k, subdict in lstore.index.items():
		print( k, subdict )
	nl()
	print('Columns changed ', lstore.changed )
	print('Rows changed   ', bin(lstore.rows_changed()) )
	# print('Rows changed indexes ', bit_indexes(lstore.rows_changed()))
	# print('Rows deleted   ', bin(lstore._deleted))  

				
if __name__ == '__main__':
				
	print('Test Script for ListStore/TupleStore ')
	nl()
	
	if gc_present:
		main_start = mem_free()
	
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
	
	nl()
	print('dir(liststore) ', dir(ls))
	nl() 
	
	ls_data = [[ 'Bill', '22 AnyWhere', '999-888-7777', 'billb@xxx.net', 17],
			   [ 'Bob K.', '44 AnyWhere But Here', '222-333-4447', 'bobk@yyy.net', 4],
			   [ 'Sally', '22 AnyWhere', '999-888-7777', 'sally@xxx.net', 0],   
			   [ 'Sam', '66 EveryWhere', '888-444-44447', 'samy@yyy.net', 1],    
			   [ 'Mary', '88 NoWhere', '888-444-0000', 'mary@zzz.net', 18]]
			   
	print('Extending list store ')
	nl()
	ls.extend(ls_data)
		
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
	
	print("ls.get(2, 'name') -> ", ls.get(2 , 'name'))
	print("ls.get(4, 'address') -> ", ls.get(4 , 'address'))
	nl()
	
	print("ls.set('address', 4, '367 SomeWhere')")
	ls.set(4, 'address', '367 SomeWhere')
	print("ls.get(4, 'address') ->", ls.get(4 , 'address'))
	nl()
	
	print("ls.set(2, 'num_of_RPZeros', 27)")
	ls.set(2, 'num_of_RPZeros', 27)
	nl()

	display_store(ls)
	nl()
	
	nl()
	print('ls.get_rows(ls.rows_changed()) ', ls.get_rows(ls.rows_changed()))
	nl()
	
	print()
	 
	
	print('try to trigger no defaults error')
	try:
		ls.append(['error','no defaults'])
	except Exception as e:
		print(e)
	else:
		print('ERROR: Shoud be an error for no defaults')
	nl()

	'''
	print('Delete/hide first three rows')
	for r in [ 0, 1, 2 ]:
		ls.delete(r)
	nl()	
	print('Deleted row indexes ', bit_indexes(ls.deleted))
	nl()
	'''
	
	print('Iterate Liststore')
	nl()
	for i, r in enumerate(iter(ls)):
		print('row ', i, r)
	nl()
	
	print('Dump ListStore ')
	nl()
	for ll in ls.dump():
		print(ll)
	nl()
	
	print('pop 0, 1 ,2 ')
	for i in bit_indexes(3):
		print('popping', i, ' -> ', ls.pop(i))
	nl()
		
	print('Dump ListStore ... no deletes to filter')
	nl()
	for ll in ls.dump():
		print(ll)
	nl()	
	
	if gc_present:
		mem_lstore = mem_free() 
	
	
	#############################   
	
	print('=== TupleStore ===')
	nl()
	

	print("ntstore = TupleStore(nt_name = 'Testing',")
	print("                column_defs= [ 'aaa', 'bbb', 'ccc', 'ddd' ],")
	print("                defaults= [ 'default3', 'default4'])")
	nl()


	ntstore = TupleStore(nt_name = 'Testing',
					column_defs= [ 'aaa', 'bbb', 'ccc', 'ddd' ],
					defaults= [ 'default3', 'default4'])
	nl()

	display_store(ntstore)
	nl()
	
	print('Use ntstore make_namedtuple method for a new Testing tuple with defaults')
	ntx = ntstore.make_namedtuple((1, 2, 3))
	print('ntstore.make_namedtuple((1, 2, 3)) -> ', ntx ) 
	nl()
	print('Use ntstore.ntuple_factory directly for a new Testing tuple (1, 2, 3 ), no defaults')
	
	try:
		mytup = ntstore.ntuple_factory(*(1, 2, 3 ))
	except Exception as e:
		print('NT Factory Error: ', e)
	
	mytup = ntstore.ntuple_factory(*(1, 2, 3, None ))
	print('ntstore.ntuple(*(1, 2, 3, None ) -> ', mytup )
	print('type(mytup)                     ', type(mytup))
	nl()
	print('No update to ntstore so far , ntstore.length = ', ntstore.length)
	nl()

	print("ntstore.append(('test66', 'always', 'rule-based', 999))") 
	ntstore.append(('test66', 'always', 'rule-based', 999))
	nl()

	
	print("ntstore.append(('test1', 'always'))")
	ntstore.append(('test1', 'always' ))
	nl()
	
	display_store(ntstore)
	nl()
	
	print("ntstore.reset_changed()")
	ntstore.reset_changed()
	nl()
	
	print("append(('test2','often', 'loot-based', 24 ))")   
	ntstore.append(('test2','often', 'loot-based', 24 ))
	
	print("append(('test2', 'sometimes', 'values_based' )")
	ntstore.append(('test2', 'sometimes', 'values_based' ))
	nl()
	print("ntstore.index_atttr('aaa')")
	ntstore.index_attr('aaa')
	nl()

	display_store(ntstore)
	nl()
	
	print('ntstore.reset_changed()')
	nl()
	
	ntstore.reset_changed()
		
	tups = [('tesxx','often', 'loot-based', None ),
			('test2','never', 'loot-based', [ 1, 2, 3 ]),
			('test2','occasionally', 'food-based', 44 ),
			('test2','often', 'luck-based', 24 ),           
			('tesxx','often', 'loot-based', ( 3, 4, 5)),
			('test2','never', 'bot-based', None ),
			('tesxx','often', 'rule-based', 24 ),
			('test2','often', 'loot-based', ( 3, 4, 5 ))]
			
	print('Extending 8 rows ...')
	nl()
			
	ntstore.extend(tups)
    
	display_store(ntstore)
	nl()
	
	print('== Reset changed ==')
	print('changed ', ntstore.changed, bin(ntstore.changed[0]))
	print('ntstore.reset_changed(7)' ) 
	ntstore.reset_changed(7)
	print('changed ', ntstore.changed, bin(ntstore.changed[0]))
	nl()
	
	print('ntstore.reset_changed()')
	nl()
	ntstore.reset_changed() 
	
	print('Pop/remove row 3 ( 4th row in the list ).  Note: requires reindexing, very slow, use discouraged !') 
	popped = ntstore.pop(3)
	print('popped tuple ', popped)
	nl()
	
	display_store(ntstore)
	nl()
	print('Note that pop does not set changed bit for row, no slot to refer to.')
	nl()
	print('May need to implement deleted int for row so can do queries like ')
	print('ls.changed & ~ls.deleted to retain changed info for row, and allow ')
	print('adjustment of the index for the popped row rather than reindexing entirely.')  
	nl()
	
	
	print('=== List Index Functions ===')
	nl()
	print('find() and find_all() functions - less memory and indexing overhead than Indexer.' )
	print('May be better for larger structures in memory-challenged micropython apps.')
	print('And they seem to run pretty fast.  ') 
	nl()
	for col, val in [('xxx', 'no val'),('aaa', 'no val'),('aaa','test2'),('bbb', 'never'), ('ccc','rule-based'), ('ddd', (3,4,5))]:
		print('column:', col , ' value: ', val )
		print('ntstore.find(col, val) -> ', ntstore.find(col, val)) 
		row_indexes = ntstore.find_all(col, val)
		print('ntstore.find_all(col, val) -> ', row_indexes )
		print('get_rows(row_indexes) ->')
		rows = ntstore.get_rows(row_indexes)
		for r in rows:
			print(r)
		nl()    
	nl()
	
	############################
	
	print('=== Indexing ===')
	nl()
	
	print('Indexer.index_list class method')
	idx = Indexer.index_list(['a','b','c','d', 'c', 'b', 'a'] )
	print("List index of ['a','b','c','d', 'c', 'b', 'a']", idx)
	nl()
	
	for at in ntstore.col_names:
		print('Indexing attr :', at)
		ntstore.index_attr(at)
	nl()
	
	print("ntstore.index['aaa'] ", ntstore.index['aaa'])
	nl()

	for k, v in ntstore.index['aaa'].items():
		print( k, bin(v))
	nl()
	
	nt = ntstore.ntuple_factory( 'aaa', 3434,  888, 23.7 )
	
	print('append ntstore.ntuple_factory ', nt )
	nl()
	
	ntstore.append(nt)
	nl()
	
	print('Index all columns - reindex()')
	ntstore.reindex()

	display_store(ntstore)
	nl()
	
	print('Skipping index tests ...')
	print()
	
	'''
	
	print("for key in ['aaa']: use bitmasks to build lists of tuples.")
	nl()
	for key in ['aaa']:
		print('Index ', key )
		for value in ntstore.index[key].keys():
			print( 'value: ', value, '      mask: ', bin(ntstore.index[key][value]))
			ntuples = ntstore.make_tuples(ntstore.index[key][value])
			for n in ntuples:
				print(n)
			nl()
		nl()
	nl()

	
	print('for k, v in index.items():')
	for key, vals in ntstore.index.items():
		print('Index for attr ', key )
		nl()
		print(vals)
		nl()
		for k, v in vals.items():
			print( k, type(k),  bin(v))
		nl()
	'''     

	print('Iterate ...')
	nl()    
	for i, nt in enumerate(iter(ntstore)):
		print(i, nt)
	nl()
	print('Raw Dump ...')
	nl()    
	print(ntstore.dump())
	nl()
	
	print('=== ListStore Queries  ===')
	nl()
	
	print("ntstore.get_rows(ntstore.index[ccc'][888]")
	print(ntstore.get_rows(ntstore.index['ccc'][888]))
	nl()
	
	print("ntstore.index['aaa']['test1'] ", ntstore.index['aaa']['test1'])
	print("ntstore.index['bbb']['always'] ", ntstore.index['bbb']['always'])
	nl()
	print("ntstore.index['aaa']['test1'] & ntstore.index['bbb']['always']")
	bmask = ntstore.index['aaa']['test1'] & ntstore.index['bbb']['always']
	print('bmask ', bin(bmask))
	print(ntstore.get_rows(bmask))
	nl()
	
	print("ntstore.index['aaa']['test1'] | ( ntstore.index['aaa']['tesxx'] & ntstore.index['ddd'][None] )")
	bmask = ntstore.index['aaa']['test1'] | ( ntstore.index['aaa']['tesxx'] & ntstore.index['ddd'][None] )
	print('bmask ', bin(bmask))
	for tp in ntstore.get_rows(bmask):
		print(tp)
	nl()
	
	print("ntstore.index['aaa']['tesxx'] & ~ntstore.index['ddd'][None]")
	bmask = ntstore.index['aaa']['tesxx'] & ~ntstore.index['ddd'][None]
	print('bmask ', bin(bmask))
	for tp in ntstore.get_rows(bmask):
		print(tp)
	nl()
	print('End of Test')
	nl()


	print('ntstore.length ', ntstore.length )
	print('Clearing ... ')
	ntstore.clear()
	print('ntstore.length ', ntstore.length )
	display_store(ntstore)
	nl()
	
	if gc_present:
		main_end = mem_free()
		print('=== Memory Usage for MicroPython ===') 
		print('Total memory started: ', mem_start )
		print('Memory use to start of __main___ :', mem_start-main_start)
		print('ListStore with instance ( 5 cols x 5 rows ): ', main_start - mem_lstore )  
		print('Total memory used: ', mem_start-main_end)
		collect()
		print('Mem after collect: ',  mem_start-mem_free()) 
		nl()
	
