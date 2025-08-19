"""
module:     liststore
version:    v0.4.4
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

Known to run on Python 3.9+, micropython v1.20-22 on a Pico and Arduino Nano ESP32. 

"""



from collections import namedtuple

# from lib.vdict import VolatileDict as vdict

try:
    from lib.core.bitops import power2, bit_indexes, bitslice_insert, bit_remove
except:
    from core.bitops import power2, bit_indexes, bitslice_insert, bit_remove

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
       
        # needs to be set via set_indexer() using Indexer class,
        # no overhead if not used
        self.indexer = None


    def __iter__(self) -> list[list]:
        """Yield columns as list of lists, an iterator over rows."""

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

    def values_changed(self, row: int) -> list[int]:
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

    def get_row(self, slot: int, asdict=False) -> list:  # or dict
        """Get a row, across all columns."""

        self.check_slot(slot)
        
        row = [self.store[i][slot] for i in range(len(self.column_names))]
        
        if asdict:
            return dict(zip(self.column_names, row ))
        else:
 
            return row
            
    def fetch_row(self, slot: int) -> list:
        """Get row with automatic reset of columns changed"""
    
        row = self.get_row(slot)
        self.reset_changed(slot)
        return row
    
    @staticmethod        
    def resolve_slots(int_or_list) -> list[int]:
    
        if isinstance(int_or_list, int):
            if int_or_list == 0:
                return []

            else:
                return bit_indexes(int_or_list)
        else:
            return int_or_list

    def get_rows(self, int_or_list) -> list[list]:
        """make rows from access mask,
        if int_or_list is type int, make list of bitindexes"""
           
        int_list = self.resolve_slots(int_or_list)

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

        if list_of_lists is None or not isinstance(list_of_lists,( list, tuple )): 
            raise ListStoreError("Extend: No input list or tuple provided.")

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
            
        # new_list is the input list with defaults

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
                len(new_list),
                (1 << (len(new_list))) - 1,
            )

        if self.indexer and self.indexer.index:
            self.indexer.extend_index(new_list)

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
    
    A bit tricky when subclassed as TableStore.  Currently, the
    namedtuple 'typename' is a type of tuple when used as TupleStore.
    When subclassed, the 'typename' is the same as the TableStore
    table name.  This can be confusing because a Table named Customer
    also has a tuple type Customer: a query Customer.find( 'name', 'Bob Smith')
    would return Customer('Bob Smith', '222 Anyroad ... etc. ).
    
    Which Customer is *the* Customer ?  Easy to fix, but has an interesting
    propery that Customer('Bob Smith' ... ) is only meaningful to the
    Customer table.  The table owns the type. We'll see how it goes.  
    """

    def __init__(
        self,
        nt_name: str,   # either nt 'type name' or nt 'table name'
        column_defs: list = None,
        defaults: list = None,
    ):

        super().__init__(column_defs, defaults)

        self.nt_name = nt_name  # either naned tuple 'typename;
        self.ntuple_factory = namedtuple(nt_name, self.column_names)

    def __iter__(self) -> list[tuple]:
        """Yeild columns as list of lists, an iterator over rows."""

        yield from [self.ntuple_factory(*row) for row in zip(*self.store)]

    def make_namedtuple(self, tup_values: list) -> tuple:
        """Make tuple with defaults according to spec., then return, no update."""

        tp = self.resolve_defaults(tup_values)
        return self.ntuple_factory(*tp)

    def get_row(self, slot: int, asdict=False) -> tuple: # or dict
        """Get row using slot, return namedtuple or dict."""
        
        row = super().get_row(slot, asdict)

        if asdict:
            return row # in dict form
        else:    
            return self.ntuple_factory(*row)

    def get_rows(self, int_or_list) -> list[tuple]:
     
        int_list = self.resolve_slots(int_or_list)
           
        return [self.get_row(i) for i in int_list]


    def pop(self, slot: int) -> tuple:
        """pop slot number"""

        popped_list = super().pop(slot)
        return self.ntuple_factory(*popped_list)

    def dump(self) -> list[tuple]:
        """ dump entire db as list of named tuples """
        yield from [self.ntuple_factory(*row) for row in zip(*self.store)]
   



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

