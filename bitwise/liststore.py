"""
module:     liststore
version:    v0.4.1
sourcecode: https://github.com/billbreit/BitWiseApps
copyleft:   2024 by Bill Breitmayer
licence:    GNU GPL v3 or above
author:     Bill Breitmayer

liststore - a column-oriented data store using a generalized list of lists structure, 
with typical list-like operations. 
           
 - an indexing store for tuples. Note that indexer can consume 
   large amounts of memory, probably too much for a 256K class platform.
   
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
    mem_start = mem_free()
except:
    gc_present = False

from collections import namedtuple

from lib.bitops import power2, bit_indexes, bitslice_insert, bit_remove

from time import localtime

# for mpy, precision gmtime/localtime is to sec. apparently
datetime_fields = [ 'year', 'mon', 'day', 'hour', 'min', 'sec']
datetime = namedtuple('datetime', datetime_fields )

def timestamp():

     return localtime()[:6]


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

    def __init__(
        self,
        column_names: list = None,
        defaults: list = None,
    ):

        if (
            column_names is None
            or not isinstance(column_names, list)
            or column_names == []
        ):
            raise ListStoreError("ListStore must have a list with at least one column.")

        super().__init__()

        self.column_names = column_names
        self.defaults = defaults or []

        self.store: list[list] = [
            [] for i in range(len(self.column_names))]
            
        self.changed:list[int] = [0] * len(self.column_names) 
       
        # needs to be set with Indexer class, no overhead if not used
        self.indexer = None 


    def __iter__(self) -> list[list]:
        """Yeild columns as list of lists, an iterator over rows."""

        yield from [list(row) for row in zip(*self.store)]

    @property
    def length(self) -> int:
        return len(self.store[0])

    def rows_changed(self) -> int:
        """Return column mask of rows changed, by ORing in each
        column changed mask yielding rows changed."""

        rc = 0
        for i in range(len(self.column_names)):
            rc |= self.changed[i]

        return rc

    # def values_changed(self, row: int) -> list[int]:
    def values_changed(self, row: int) -> list:
        """Column indexes for values changed in a given row, probably working
        back from the return of rows_changed(). The values are then
        store[col][row1...col_len]"""

        column_indexes = [
            i for i in range(len(self.column_names)) if power2(row) & self.changed[i]
        ]

        return column_indexes

    def reset_changed(self, slot: int = None):
        """Reset changed mask for row slot or if slot is None, reset changed for all columns."""

        if slot:
            self.check_slot(slot)

        for i in range(len(self.column_names)):
            if slot is not None:
                self.changed[i] &= ~power2(slot)
            else:
                self.changed[i] = 0

    def resolve_defaults(self, in_list: list) -> list:
        """Apply defaults, from end ( right to left )"""
    
        if len(in_list) == 0 or len(in_list) > len(self.column_names):
            raise ListStoreError(
                "Default Error: input length must greater than zero or less than len(col_names)."
            )

        if len(self.defaults) + len(in_list) < len(self.column_names):
        
            raise ListStoreError(
                "Default Error: Not enough defaults to fill missing values."
            )
            
        if len(in_list) == len(self.column_names):
            return in_list
            
        ilist = list(in_list)
        defs_needed = len(self.column_names) - len(ilist)
        dlist = self.defaults[-defs_needed:]

        for d in dlist:
            if callable(d):
                ilist.append(d())
            else:
                ilist.append(d)

        return ilist

    def check_slot(self, slot: int):

        if slot < 0:
            raise ListStoreError(f"Slot number {slot} must greater than 0.")

        if slot > len(self.store[0]):
            raise ListStoreError(
                f"Slot number {slot} is greater than len of ListStore."
            )

    def slot_for_col(self, col_name: str) -> int:
        """slot number for column name"""

        try:
            index = self.column_names.index(col_name)
        except ValueError:
            raise ListStoreError(
                f"Get Slot for Column Error: bad column name '{col_name}'"
            )

        return index

    def get(self, slot: int, col_name: str):
        """Get single slot from a column."""

        self.check_slot(slot)

        return self.get_column(col_name)[slot]

    def get_column(self, col_name: str) -> list:
        """Return a list of values for 'col_name'."""

        return self.store[self.slot_for_col(col_name)]

    def get_row(self, slot: int) -> list:
        """Get a row, across all columns."""

        self.check_slot(slot)

        return [self.store[i][slot] for i in range(len(self.column_names))]

    def get_rows(self, int_or_list) -> list[list]:
        """make rows from access mask,
        if int_or_list is type int, make list of bitindexes"""

        if isinstance(int_or_list, int):
            if int_or_list == 0:
                return []

            else:
                int_list = bit_indexes(int_or_list)
        else:
            int_list = int_or_list

        return [self.get_row(i) for i in int_list]

    def set(self, slot: int, col_name: str, value):
        """Set col_name (attr) in slot int to value"""

        self.check_slot(slot)

        col_slot = self.slot_for_col(col_name)

        old_value = self.store[col_slot][slot]

        self.store[col_slot][slot] = value
        
        if self.indexer:
            self.indexer.update_index(col_name, slot, old_value, value)

        self.changed[col_slot] |= power2(slot)

    def append(self, in_list: list = None):
        """Append to list and update index with append_index.
        No need to index_attr entire column, all bitmasks
        will stll be valid."""

        if in_list is None:
            raise ListStoreError("Append: list passed can not be None")

        # defaults
        if len(in_list) != len(self.store):
            if self.defaults:

                in_list = self.resolve_defaults(in_list)

            else:
                raise ListStoreError(
                    "Append: List missing values and no defaults defined."
                )

        ilist = list(in_list)

        for i, v in enumerate(ilist):
            self.store[i].append(v)

        for i in range(len(ilist)):
            self.changed[i] |= power2(len(self.store[0]) - 1)

        if self.indexer and self.indexer.index:
            self.indexer.append_index(ilist)

    def extend(self, list_of_lists: list = None):
        """Works esentially the same as list extend.  An error 
           in any of the new rows prevents update of all rows
           in the list, something like a database transaction."""   

        if list_of_lists is None:
            raise ListStoreError("Extend: No input list provided.")

        # resolve defaults
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
                    raise ListStoreError(
                        "Extend Error: List missing values and no defaults defined."
                    )
            else:
                new_list.append(lst)

        if len(errs) > 0:
            raise ListStoreError("Extend Error: Not enough values or defaults", errs)

        save_top = self.length  # top_bit, that is last bit + 1

        # transpose list of rows to list of columns
        col_list = [lcol for lcol in zip(*new_list)]

        for i, column in enumerate(self.store):
            self.store[i].extend(col_list[i])

        for i in range(len(self.store)):
            # insert to the right of last bit index + 1
            self.changed[i] = bitslice_insert(
                self.changed[i],
                save_top,
                len(list_of_lists),
                (1 << (len(list_of_lists))) - 1,
            )

        if self.indexer and self.indexer.index:
            self.indexer.extend_index(list_of_lists)

    def pop(self, row: int) -> list:
        """Remove slots in liststore for a given row, and update all int
        bitmasks by AND NOT to all values in attr subdicts. Guarantees
        bitmask references but slow, maybe several milliseconds on
        a microcontroller.  Need to test?
        Note no default for pop(), user needs to implement as pop(0)
        FIFO or pop(len(list)-1) LIFO, pop(-1) won't pass check_slot."""

        self.check_slot(row)

        popped_row = [self.store[i].pop(row) for i in range(len(self.column_names)) ]

        for i in range(len(self.column_names)):
            self.changed[i] = bit_remove(self.changed[i], row)

        # self.indexer.reindex()
        if self.indexer:
            self.indexer.pop_index(row)  # may be faster ?

        return popped_row

    def clear(self):
        """Empty liststore data , reset changed, clear Indexer"""

        if len(self.column_names) == 0:
            return

        for i in range(len(self.column_names)):
            self.store[i] = []

        self.reset_changed()
        
        if self.indexer:
            self.indexer.clear()

        return

    def dump(self) -> list[list]:
        """Dump all rows as List[List]"""
        yield from [list(row) for row in zip(*(self.store))]

    def find(self, col_name: str, value, start=0) -> int:
        """Return the first row number for match value in column."""

        try:
            i = self.get_column(col_name).index(value, start)
        except ValueError:
            i = -1

        return i

    def find_all(self, col_name: str, value) -> list[int]:
        """Return list of slot numbers for all match values in column."""

        slot_index = self.slot_for_col(col_name)
        il = []
        start = 0
        i = 0

        while i > -1:
            try:
                i = self.store[slot_index].index(value, start)
                il.append(i)
                start = i + 1
            except ValueError:
                i = -1

        return il

    """ Index Methods """
    
    def set_indexer(self, indexer_cls:'IndexerClass' = None, usertypes:list = None ):
        """Create indexer with external *class* instance.  Awkward, but this
        allows basic ListStore to avoid the overhead of importing the
        Indexer class and may save a significant amount of working memory
        for the import ( says 13K -> 9K ? ). Ref should be OK, but check __del__.
        The methods find and find_all can do much the same with less memory. """
        
        if not indexer_cls or not isinstance(indexer_cls, type ):
            raise ListStoreError('Set index function needs Indexer class.')
        
        self.indexer = indexer_cls(self.column_names,
                                   self.store,
                                   usertypes if usertypes else [] )

    @property
    def index(self) -> dict:
    
        if self.indexer:
            return self.indexer.index

    def index_attr(self, attr_name: str):
        """Create new index for attr.column name"""

        if self.indexer:
            self.indexer.index_attr(attr_name)

    def drop_attr(self, attr_name: str):
        """Delete index for attr.column name"""

        if self.indexer:
            self.indexer.drop_attr(attr_name)

    def reindex(self):
        """Rebuild entire index, may be slow for large store"""
        if self.indexer:
            self.indexer.reindex()


class TupleStoreError(Exception):
    pass


class TupleStore(ListStore):
    """List-like storage for tuples, impemented with
    columns rather than rows.  Updatable without new instance.
    """

    def __init__(
        self,
        nt_name: str,
        column_defs: list = None,
        defaults: list = None,
    ):

        super().__init__(column_defs, defaults)

        self.nt_name = nt_name
        self.ntuple_factory = namedtuple(nt_name, self.column_names)

    def __iter__(self) -> list[tuple]:
        """Yeild columns as list of lists, an iterator over rows."""

        yield from [self.ntuple_factory(*row) for row in zip(*self.store)]

    def make_namedtuple(self, tup_values: list) -> tuple:
        """Make tuple with defaults according to spec., then return, no update."""

        tp = self.resolve_defaults(tup_values)
        return self.ntuple_factory(*tp)

    def get_row(self, slot: int) -> tuple:
        """Get row using slot, return namedtuple."""
        row = super().get_row(slot)
        return self.ntuple_factory(*row)

    def get_rows(self, int_or_list) -> list[tuple]:

        return [self.ntuple_factory(*row) for row in super().get_rows(int_or_list)]

    def pop(self, slot: int) -> tuple:
        """pop slot number"""

        popped_list = super().pop(slot)
        return self.ntuple_factory(*popped_list)

    def dump(self) -> list[tuple]:
        """ dump entire db as list of named tuples """
        yield from [self.ntuple_factory(*row) for row in zip(*self.store)]
        # return [self.ntuple_factory(*row) for row in zip(*self.store)]





def display_store(lstore):
    print("Store type  ", type(lstore))
    print("Length      ", lstore.length)
    # nl()
    for attr, col_store in zip(lstore.column_names, lstore.store):
        print("Column ", attr, col_store)
    print()
    if lstore.index:
        print("Index ")
        for k, subdict in lstore.index.items():
            print(k, subdict)
        print()
    print("Columns changed ", lstore.changed)
    print("Rows changed   ", bin(lstore.rows_changed()))
    # print('Rows changed indexes ', bit_indexes(lstore.rows_changed()))
    # print('Rows deleted   ', bin(lstore._deleted))


if __name__ == "__main__":


    # Indexer class only usable with ListStore 


#    from indexer import Indexer   # delta to below is 4K ???  
    

    print("Test Script for ListStore/TupleStore ")
    nl()
    

    if gc_present:
        main_start = mem_free()
        
    from lib.indexer import Indexer

    try:
        la = ListStore("BadTest")
    except Exception as e:
        print("Exception: ", e)
        nl()
    else:
        print("ERROR: Should be Exception - woops.")
        nl()

    print("Create ListStore(['name','address', 'phone', 'email', 'num_of_RPZeros'])")
    nl()

    ls = ListStore(["name", "address", "phone", "email", "num_of_RPZeros"])
    ls.set_indexer(Indexer)

    nl()
    print("dir(liststore) ", dir(ls))
    nl()

    ls_data = [
        ["Bill", "22 AnyWhere", "999-888-7777", "billb@xxx.net", 17],
        ["Bob K.", "44 AnyWhere But Here", "222-333-4447", "bobk@yyy.net", 4],
        ["Sally", "22 AnyWhere", "999-888-7777", "sally@xxx.net", 0],
        ["Sam", "66 EveryWhere", "888-444-44447", "samy@yyy.net", 1],
        ["Mary", "88 NoWhere", "888-444-0000", "mary@zzz.net", 18],
    ]

    print("Extending list store ")
    nl()
    ls.extend(ls_data)

    ls.reindex()

    display_store(ls)
    nl()

    print("ls.reset_changed()")
    nl()
    ls.reset_changed()

    print("Index address and num_of_RPZeros")
    ls.index_attr("address")
    ls.index_attr("num_of_RPZeros")
    nl()

    print("ls.get(2, 'name') -> ", ls.get(2, "name"))
    print("ls.get(4, 'address') -> ", ls.get(4, "address"))
    nl()

    print("ls.set(4 , 'address', '367 SomeWhere')")
    ls.set(4, "address", "367 SomeWhere")
    print("ls.get(4, 'address') ->", ls.get(4, "address"))
    nl()

    print("ls.set(2, 'num_of_RPZeros', 27)")
    ls.set(2, "num_of_RPZeros", 27)
    nl()

    display_store(ls)
    nl()

    nl()
    print("ls.get_rows(ls.rows_changed()) ", ls.get_rows(ls.rows_changed()))
    nl()

    print()

    print("try to trigger no defaults error")
    try:
        ls.append(["error", "no defaults"])
    except Exception as e:
        print(e)
    else:
        print("ERROR: Shoud be an error for no defaults")
    nl()

    """
	print('Delete/hide first three rows')
	for r in [ 0, 1, 2 ]:
		ls.delete(r)
	nl()	
	print('Deleted row indexes ', bit_indexes(ls.deleted))
	nl()
	"""

    print("Iterate Liststore")
    nl()
    for i, r in enumerate(iter(ls)):
        print("row ", i, r)
    nl()

    print("Dump ListStore ")
    nl()
    for ll in ls.dump():
        print(ll)
    nl()

    print("pop 0, 1 ")
    for i in bit_indexes(3):
        print("popping", i, " -> ", ls.pop(i))
    nl()

    print("Dump ListStore ... no deletes to filter")
    nl()
    for ll in ls.dump():
        print(ll)
    nl()

    if gc_present:
        mem_lstore = mem_free()

    #############################

    print("=== TupleStore ===")
    nl()

    print("ntstore = TupleStore(nt_name = 'Testing',")
    print("                column_defs= [ 'aaa', 'bbb', 'ccc', 'ddd' ],")
    print("                defaults= [ 'default3', timestamp])")
    print("                indexer = Indexer()")
    nl()

    ntstore = TupleStore(
        nt_name="Testing",
        column_defs=["aaa", "bbb", "ccc", "ddd"],
        defaults=["default3", timestamp],
    )
    ntstore.set_indexer(Indexer)
    nl()

    display_store(ntstore)
    nl()

    print("Use ntstore make_namedtuple method for a new Testing tuple with defaults")
    ntx = ntstore.make_namedtuple((1, 2, 3))
    print("ntstore.make_namedtuple((1, 2, 3)) -> ", ntx)
    nl()
    print(
        "Use ntstore.ntuple_factory directly for a new Testing tuple (1, 2, 3 ), no defaults"
    )

    try:
        mytup = ntstore.ntuple_factory(*(1, 2, 3))
    except Exception as e:
        print("NT Factory Error: ", e)

    mytup = ntstore.ntuple_factory(*(1, 2, 3, None))
    print("ntstore.ntuple(*(1, 2, 3, None ) -> ", mytup)
    print("type(mytup)                     ", type(mytup))
    nl()
    print("No update to ntstore so far , ntstore.length = ", ntstore.length)
    nl()

    print("ntstore.append(('test66', 'always', 'rule-based', 999))")
    ntstore.append(("test66", "always", "rule-based", 999))
    nl()

    print("ntstore.append(('test1', 'always'))")
    ntstore.append(("test1", "always"))
    nl()

    display_store(ntstore)
    nl()

    print("ntstore.reset_changed()")
    ntstore.reset_changed()
    nl()

    print("append(('test2','often', 'loot-based', 24 ))")
    ntstore.append(("test2", "often", "loot-based", 24))

    print("append(('test2', 'sometimes', 'values_based' )")
    ntstore.append(("test2", "sometimes", "values_based"))
    nl()
    print("ntstore.index_atttr('aaa')")
    ntstore.index_attr("aaa")
    nl()

    display_store(ntstore)
    nl()

    print("ntstore.reset_changed()")
    nl()

    ntstore.reset_changed()

    tups = [
        ("tesxx", "often", "loot-based", None),
        ("test2", "never", "loot-based", [1, 2, 3]),
        ("test2", "occasionally", "food-based", 44),
        ("test2", "often", "luck-based", 24),
        ("tesxx", "often", "loot-based", (3, 4, 5)),
        ("test2", "never", "bot-based", None),
        ("tesxx", "often", "rule-based", 24),
        ("test2", "often", "loot-based", (3, 4, 5)),
    ]

    print("Extending 8 rows ...")
    nl()

    ntstore.extend(tups)

    display_store(ntstore)
    nl()

    print("Reset changed function")
    print("changed ", ntstore.changed, bin(ntstore.changed[0]))
    print("ntstore.reset_changed(7)")
    ntstore.reset_changed(7)
    print("changed ", ntstore.changed, bin(ntstore.changed[0]))
    nl()

    print("ntstore.reset_changed()")
    nl()
    ntstore.reset_changed()

    print("Pop/remove row 3 ( 4th row in the list ).")
    popped = ntstore.pop(3)
    print("popped tuple ", popped)
    nl()
    print("Note: pop() requires index adjustment or reindexing, both are slow, use discouraged !"
    )
    nl()
    display_store(ntstore)
    nl()
    print("Note that pop does not set changed bit for row, no slot to refer to.")
    nl()
    print("May need to implement deleted int for row so can do queries like ")
    print("ls.changed & ~ls.deleted to retain changed info for row, and allow ")
    print("adjustment of the index for the popped row rather than reindexing entirely.")
    nl()

    print("=== List Find Functions ===")
    nl()
    print(
        "find() and find_all() functions - less memory and indexing overhead than Indexer."
    )
    print("May be better for larger structures in memory-challenged micropython apps.")
    print("And they seem to run pretty fast ( need more numbers ).  ")
    nl()
    for col, val in [
        ("xxx", "no val"),
        ("aaa", "no val"),
        ("aaa", "test2"),
        ("bbb", "never"),
        ("ccc", "rule-based"),
        ("ddd", (3, 4, 5)),
    ]:
        print("column:", col, " value: ", val)
        try:
            sl = ntstore.find(col, val)
            print("ntstore.find(col, val) -> ", sl)
        except Exception as e:
            print("find Error: ", e)
        try:
            row_indexes = ntstore.find_all(col, val)
            print("ntstore.find_all(col, val) -> ", row_indexes)
        except Exception as e:
            print("find_all Error: ", e)
            row_indexes = []
        print("get_rows(row_indexes) ->")
        rows = ntstore.get_rows(row_indexes)
        for r in rows:
            print(r)
        nl()
    nl()

    ############################

    print("=== Indexing ===")
    nl()

    print("Indexer.index_list class method")
    idx = Indexer.index_list(["a", "b", "c", "d", "c", "b", "a"])
    print("List index of ['a','b','c','d', 'c', 'b', 'a']", idx)
    for k,v in idx.items():
        print( k , bin(v))
    nl()

    for at in ntstore.column_names:
        print("Indexing attr :", at)
        ntstore.index_attr(at)
    nl()

    print("ntstore.index['aaa'] ", ntstore.index["aaa"])
    nl()

    for k, v in ntstore.index["aaa"].items():
        print(k, bin(v))
    nl()

    nt = ntstore.ntuple_factory("aaa", 3434, 888, 23.7)

    print("append ntstore.ntuple_factory ", nt)
    nl()

    ntstore.append(nt)
    nl()

    print("Index all columns - reindex()")
    ntstore.reindex()

    display_store(ntstore)
    nl()

    print("Skipping index tests ...")
    print()

    """
	
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
	"""

    print("Iterate ...")
    nl()
    for i, nt in enumerate(iter(ntstore)):
        print(i, nt)
    nl()
    print("Raw Dump ...")
    nl()
    print('ntstore.dump() ', ntstore.dump())
    nl()
    for ll in ntstore.dump():
        print(ll)
    nl()
    nl()

    print("=== ListStore Queries  ===")
    nl()

    print("ntstore.get_rows(ntstore.index[ccc'][888]")
    print(ntstore.get_rows(ntstore.index["ccc"][888]))
    nl()

    print("ntstore.index['aaa']['test1'] ", ntstore.index["aaa"]["test1"])
    print("ntstore.index['bbb']['always'] ", ntstore.index["bbb"]["always"])
    nl()
    print("ntstore.index['aaa']['test1'] & ntstore.index['bbb']['always']")
    bmask = ntstore.index["aaa"]["test1"] & ntstore.index["bbb"]["always"]
    print("bmask ", bin(bmask))
    print(ntstore.get_rows(bmask))
    nl()

    print(
        "ntstore.index['aaa']['test1'] | ( ntstore.index['aaa']['tesxx'] & ntstore.index['ddd'][None] )"
    )
    bmask = ntstore.index["aaa"]["test1"] | (
        ntstore.index["aaa"]["tesxx"] & ntstore.index["ddd"][None]
    )
    print("bmask ", bin(bmask))
    for tp in ntstore.get_rows(bmask):
        print(tp)
    nl()

    print("ntstore.index['aaa']['tesxx'] & ~ntstore.index['ddd'][None]")
    bmask = ntstore.index["aaa"]["tesxx"] & ~ntstore.index["ddd"][None]
    print("bmask ", bin(bmask))
    for tp in ntstore.get_rows(bmask):
        print(tp)
    nl()
    print("End of Test")
    nl()

    print("ntstore.length ", ntstore.length)
    print("Clearing ... ")
    ntstore.clear()
    print("ntstore.length ", ntstore.length)
    display_store(ntstore)
    nl()

    if gc_present:
        main_end = mem_free()
        print("=== Memory Usage for MicroPython ===")
        print("Total memory started: ", mem_start)
        print("Memory use to start of __main___ :", mem_start - main_start)
        print("ListStore with instance ( 5 cols x 5 rows ): ", main_start - mem_lstore)
        print("Total memory used: ", mem_start - main_end)
        collect()
        print("Mem after collect: ", mem_start - mem_free())
        nl()
        # print('locals()')
        # print(locals())   # shows partial objs
        
        

