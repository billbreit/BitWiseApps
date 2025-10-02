

try:
    from gc import mem_free, collect
    gc_present = True
    mem_start = mem_free()
except ImportError:
    gc_present = False

try:
    import fsinit
except ImportError:
    import tests.fsinit as fsinit
del(fsinit)



# from lib.bitops import power2, bit_indexes, bitslice_insert, bit_remove

from lib.core.bitops import bit_indexes

from lib.tuplestore import ListStore, TupleStore, display_store, timestamp


if __name__ == "__main__":

    nl = print 

    # Indexer class only usable with ListStore/TupleStore


#    from lib.indexer import Indexer   # delta to below is 4K ???  
    

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
    
    print("ls.get_row(4)")
    print(ls.get_row(4))
    nl()
    
    print("ls.get_row(4, asdict=True)")
    print(ls.get_row(4, asdict=True))
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
    nl()
    
    ntstore = TupleStore(
        nt_name="Testing",
        column_defs=["aaa", "bbb", "ccc", "ddd"],
        defaults=["default3", timestamp],
    )
    
    print('ntstore.set_indexer(Indexer)')
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
 
    print('ntstore.get_row(1)')   
    print(ntstore.get_row(1))
    nl()
    
    print('ntstore.get_row(1, asdict=True)')   
    print(ntstore.get_row(1, asdict=True))
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
    print("ntstore.reset_changed(5)")
    ntstore.reset_changed(5)
    print("ntstore.fetch_row(7)")
    print(ntstore.fetch_row(7))
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

    print("ntstore.index['aaa']['test1'] ", bin(ntstore.index["aaa"]["test1"]))
    print("ntstore.index['bbb']['always'] ", bin(ntstore.index["bbb"]["always"]))
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
        
        

