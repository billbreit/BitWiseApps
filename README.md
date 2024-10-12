### BitWiseApps

A toolkit for creating small footprint, high performance applications with Binary Logic on Python and MicroPython platforms.

All programs herein are 'under development', some parts maybe at the mid-moving-toward-late beta phase, others not.

Almost all of them will run under both Python 3.9+ and MicroPython 1.20+ on the RP Pico and Arduino Nano ESP32.

The directory structure:

#### bitwise dir >

Current working modules:

**iomapper.py**: A library for generalizing external bind requests, saving a lot of gory details about call structure and parameters.  Wtih a little logic thrown into the mix, it should provide a foundation for a farily simple process controller.   

#### bitwise/tests directory >

Basic tests/demos of major components:

**liststore and tablestore tests**:  taking liststore and tablestore out for a spin.  Much more fun than writing unit tests, although it may wind up with unit tests eventually.

**rpzc_demo.py**: An extended demo of DataStore.  A non-trivial demo database of 7 tables and maybe 40 rows.

Budgets are tight, tensions are mounting, the entrenched old guard may be facing a life-or-death power struggle with younger members.  A time of revolution looms !  ( But not in this version of the demo.  Once I figure out an idiom for generator queries, then let slip discord and mayhem in the Raspberry Pi Zero Club. ) 

**testinit333.py**: A temporary test for a initialize filesystem function, still in development

#### bitwise/dev directory >

Experimental test stuff, mostly for bitwise/binary operations.  

#### bitwise/lib directory >

A base of common core Python/MicroPython libraries, slowly enlarging.  Note: the '/lib' directory is in the default sys.path for micropython, the 'micropythonic standard'.

**liststore.py** - a multilist structure of columns and rows.  Intended to be quick and flexible: any row of any column can be of any valid Python type.  For a demo, run as 'python liststore.py'.
    
**tablestore.py** - a relational-like structure based on liststore with restrictions that implement:

*Python Types*: enforce column type for any Python type that can be stored/recovered from JSON. 

*Persistence*: save and restore a list of lists structure to/from a JSON file.  Restore tuple and namedtuple types not recognized by json.   
*Uniqueness Constraints*: a key column or set of columns must form a unique key, in effect, naming a row.

*Referential Integrity*: When multiple tables are defined within the DataStore class, the relationships between ( single column ) keys in tables are maintained: every child key must have a parent key and no parent with children can be deleted.

**vdict.py** - VolatileDict for tracking changes to values in a dictionary.  Also provides read-only ( write-once ) locks on value updates. 
 In a micropython environment, provides a faster alternative to mpy OrderedCollection ( default dict is not ordered ). 

Most programs run in a small memory footprint, a base of about 40K, usable on anything from Raspberry Pi Pico and ESP32 microcontrollers to ... who knows what ( Windows and Linux, not sure about Mac ). 

The current version is somewhere around 0.4.4. no matter what the code may say.  Last major update was mid-July.

 

See [Wiki Page](https://github.com/billbreit/BitWiseApps/wiki)
