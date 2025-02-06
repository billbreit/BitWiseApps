
try:
    from lib.bitops import power2, bit_indexes, bitslice_insert, bit_remove
except:
    from bitops import power2, bit_indexes, bitslice_insert, bit_remove

class IndexerError(Exception):
    pass


class Indexer(object):
    """Indexer for a values in a list of lists"""

    _indexable = [str, int, tuple, type(None)]

    def __init__(
        self,
        col_names: list[str] = None,
        store: list[list] = None,
        usertypes: list = None,
        *args,
        **kwargs,
    ):

        super().__init__()

        if col_names is None or len(col_names) == 0:
            raise IndexerError(
                "Indexer: A list of column keys must provided to Indexer."
            )

        self._slots: list[str] = col_names
        self._store = store or []  # empty liststore means class methods only
        self._index: dict = {}
        
        # list of columns actually indexed, using index_attr()
        self._indexed: list[str] = []

        if usertypes:
            self._indexable.extend(usertypes)

        self._indexable = tuple(self._indexable)   # set ?

    @classmethod
    def index_list(cls, alist: list) -> dict:
        """index values in a list or tuple"""

        """Build set of distinct, indexable values in alist"""
        col_value_set = { value for value in alist if type(value) in cls._indexable }
        

        """ init subdict """
        sub_dict = { value:0 for value in col_value_set }

        """ iterate through alist and add/update int bit mask
            values in subdict """

        for i, value in enumerate(alist):
            if type(value) in cls._indexable:
                sub_dict[value] |= power2(i)

        return sub_dict

    @property
    def index(self):
        """return ref to internal index."""
        return self._index
        
    def clear(self):
    
        self._index = {}
        self._indexed = []
        
        

    def index_attr(self, attr_name: str):
        """Create new index for attr.column name"""

        if attr_name not in self._slots:
            raise IndexerError("Index Attr: Column ", attr_name, " not known.")

        storage_slot = self._slots.index(attr_name)
        
        sub_dict = self.index_list(self._store[storage_slot])

        self._index[attr_name] = sub_dict
        if attr_name not in self._indexed:
            self._indexed.append(attr_name)

    def drop_attr(self, attr_name: str):
        """Drop indexing for an attribute/column name."""

        del self.index[attr_name]
        self._indexed.remove(attr_name)

    def update_index(self, attr_name: str, row_slot: int, old_value, new_value):
        """An altered row via set().  Need to unset bit on old value and
        set bit for new value."""

        if attr_name not in self._indexed:
            return

        # NOTAND old value 
        self.index[attr_name][old_value] &= ~power2(row_slot)

        if self.index[attr_name][old_value] == 0:
            del self.index[attr_name][old_value]
        
        # If value is new, init mask
        if type(new_value) in self._indexable:
            if new_value not in self.index[attr_name].keys():
                self.index[attr_name][new_value] = 0
                
        # OR new value
        self.index[attr_name][new_value] |= power2(row_slot)


    def append_index(self, list_in: list):
        """New slot value, for appended row. No need to rebuild masks, just OR in new offset."""

        for col_name in self._index.keys():

            store_slot = self._slots.index(col_name)
            new_slot = len(self._store[store_slot])  # current new slot

            if list_in[store_slot] not in self._index[col_name]:
                self._index[col_name][list_in[store_slot]] = 0

            self._index[col_name][list_in[store_slot]] |= power2(new_slot)

    def extend_index(self, list_of_lists: list[list]):
        """Use append index for multiple new values"""

        for ls in list_of_lists:
            self.append_index(ls)

    def pop_index(self, row_slot: int):
        """Delete one bit from masks in each subdict for indexed attr names.
           This is an alternative to reindexing entirely, may be faster ? """

        for attr_name in self._indexed:
            for key, value in self.index[attr_name].items():
                self.index[attr_name][key] = bit_remove( self.index[attr_name][key],
                                                         row_slot )

    def reindex(self):
        """build or rebuild index completely, after row pop/remove."""

        for attr_name in self._indexed:
            self.index_attr(attr_name)

    def reset(self):
        """Clear all indexes."""

        self._index = {}
        self._indexed = []

    def query(self, col_name: str, indexed_value):
        """-> Query( col_name, indexed_value, bitint"""
        pass
