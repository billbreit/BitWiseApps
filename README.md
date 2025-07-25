### BitWiseApps

A toolkit for creating small footprint, high performance applications with Binary Logic on Python and MicroPython platforms.

All programs herein are 'under development', some parts maybe at the mid-moving-toward-late beta phase, others not.

Almost all of them will run under both Python 3.9+ and MicroPython 1.20+ on the RP Pico and Arduino Nano ESP32.

The directory structure:

#### bitwise dir >

Current work-in-progress modules:

**iomapper.py**: A module for generalizing external bind requests, saving a lot of gory details about call structure and parameters.  With a little logic thrown into the mix, it should provide a foundation for a fairly simple process engine.

IOMapper needs critical attention in two areas: marshalling/shoehorning parameters and handling exceptions.  Currently, the mapper is doing nothing to handle exceptions.  To keep the controller/process engine moving, it may be better to let the caller do the deciding, or maybe just 'neuter' the exceptions into error messages in the values_dict.  Explicitly raising IOMapper exceptions should probably be limited to the initial validation of iomap.

Another major issue is debugging the defintion of the IOMap.  The IOMapper approach is as bug-free as the equivalent Python code would be, which is to say not bug free.  The advantage is that the definition bugs are all in one place rather than scattered through multi-Ks of code.  There a few tools to help debug a particular iomap - there need to be more.  See [IOMapper](https://github.com/billbreit/BitWiseApps/wiki/IOMapper) wiki page.

**fan_example.py**: A non-trivial example of IOMapper using a product design simulation for a cheap and outrageously unreliable fan, made with the cheapest parts availible ( with a one week money-back guarantee, which is slightly shorter than the expected life-time of the fan ).  Be prepared for the dreaded DEADFAN exception !  Hey, I had to do the grind for multiple decades, so have some fun in my declining years.

The fan example may also provide a basis for a simulation of a fairly complicated solar-powered water pump, to serve wildlife in deep drought situations.  See [Water for Wildlife project](https://github.com/billbreit/BitWiseApps/wiki/WaterForWildlife).

#### bitwise/lib directory >

A base of common core Python/MicroPython libraries, slowly enlarging.  Note: the '/lib' directory is in the default sys.path for micropython, the 'micropythonic standard'.

**liststore.py** - a multilist structure of columns and rows.  Intended to be quick and flexible: any row of any column can be of any valid Python type.  Also allows indexing of immutable values ( values that can be dict keys ) and bitwise operations for fast queries.  For a demo, go the the /tests directory and run as 'python liststore_test.py' ( same for other modules ).
    
**tablestore.py** - a relational-like structure based on liststore with restrictions that implement:

*Python Types*: enforce column type for any Python type that can be stored/recovered from JSON. 

*Persistence*: save and restore a list of lists structure to/from a JSON file.  Restore tuple and namedtuple types not recognized by json.

*Uniqueness Constraints*: a key column or set of columns must form a unique key, in effect, naming a row.

*Referential Integrity*: When multiple tables are defined within the DataStore class, the relationships between ( single column ) keys in tables are maintained: every child key must have a parent key and no parent with children can be deleted.

**vdict.py** - VolatileDict for tracking changes to values in a dictionary.  Also provides read-only ( write-once ) locks on value updates.  In a MicroPython environment, provides a faster alternative to mpy OrderedDict ( default dict is not ordered ).

#### bitwise/tests directory >

Basic tests/demos of major components:

**liststore, tablestore and vdict tests**:  taking liststore, tablestore and vdict out for a spin.  Much more fun than writing unit tests, although it may wind up with unit tests eventually.

**rpzc_demo.py**: An extended demo of DataStore.  A non-trivial demo database of 7 tables and maybe 40 rows.

> Budgets are tight, tensions are mounting, the entrenched old guard may be facing a life-or-death power struggle with younger members.  A time of revolution looms !

But not in this version of the demo.  Once I figure out an idiom for generator queries, then let slip discord and mayhem in the Raspberry Pi Zero Club. 

**testinit333.py**: A temporary test for a initialize filesystem function, still in development

#### bitwise/dev directory >

Experimental test stuff, mostly for bitwise/binary operations.

The file system init ( fsinit ) experiment has been a huge hastle.  MircoPython has no relative import, so I have struggled mightly to find a general solution to the import problems that plagued Python 2 and early Python 3.  Just when it seems fixed, phuuut, it's not !  Still looking for the sweet spot ...  

Most programs run in a small memory footprint, a base of about 40K, usable on anything from Raspberry Pi Pico and ESP32 microcontrollers to ... who knows what ( Windows and Linux, not sure about Mac ). 

The current version is somewhere around 0.4.6. no matter what the code may say.  Last major update was early January.

See [Home Wiki Page](https://github.com/billbreit/BitWiseApps/wiki)
