README.txt for Bill Breitmayer's BitWiseApps, a GitHub project
to bring back old-time binary logic applications into the mainstream.

My focal areas are:

- Binary Logic Applications, in this incarnation basically mapping into
  lists using integer index-slot representations and using bitwise
  operations ( such as AND &, OR |, XOR ^, NOT ~ ) for super-fast queries. 

- Cross-Python libraries, including core Python and micropython, and
  when possible Circuit Python, or any other worthy Python dialect.

The first example was bitlogic.py, a ones-complement wrapper in a 
two-complement world - for debugging, not deployment.  The next 
was bitslice.py for performing "bit surgery",  These will provide a
foundation for developing what I call "binary logic applications".

In the past months:

* iomapper.py - A module for generalizing external bind requests.  In a world of movers and 
  shakers, iomapper is a doer, a work engine.  It separates the unconditional logic from the 
  conditional logic driving the iomapper.  A few conditional rules can describe fairly 
  complex behaviors using the IOMapper class.   

* fan_example.py - A simulation of the workings of a remarkably unuseful 'smart fan', slogan: 
  "A Fan That's Smarter Than The People Who Buy It". 

In the past year:

* liststore.py - a list of lists structure with basic access and update methods,
  tracking changes to columns and rows, and column indexing for fast queries. 

* tablestore.py - a in-memory database/graph-like structure with Python types for columns,
  unique table keys, inter-table key reference integrity and a simple
  JSON save/load mechanism.

* vdict.py - VolatileDict Class, for tracking rapidly-changing values in a dictionary 
  structure.  Keys are more or less static and can be locked as read-only.   Default dict has 
  ordered keys since Python 3.6, but MicroPython is based on Python 3.4. The vdict class
  is a plug-in replacement for OrderedDict in MicroPython ( except for popitem, which defies 
  any use-case I can imagine ) with slightly better performance in older versions of mpy.

The overall development phase is maybe mid beta, excluding an envisioned asynchronous 
framework/mechanism based on asyncio, which may be in the post pre-alpha stage.

Known compatibility is Python v3.9+ and micropython v1.20-22.0, running on
the Raspberry Pi Pico and the Arduino Nano ESP 32. 

To run a __name__=='__main__': style test script, start up a decent
terminal, change current directory to point to /tests and run: 

python liststore_test.py

python tablestore_test.py

The big challenge is to reduce memory footprint for micro-controller platforms such
as the Raspberry Pi Pico and the Arduino Nano ESP 32, with 256KB and 512KB of "primary"
static RAM respectively, before allocating 80-100KB for heap memory.

On the Pico using gc.mem_free, the basic classes and functions ( at this point, Feb 2025 )
consume about 10KB ( after clearing import working memory with gc.collect ) at the start
of the test script.  The test scripts consume about 20-30KB total memory at the end of
the script. In a practical application, a TableStore or ListStore structure of a hundred
rows ( assuming 200 bytes per row ) might consume a total of 40-50K. 

Still in beta, but it's moving along ... see https://github.com/billbreit/BitWiseApps/


     
