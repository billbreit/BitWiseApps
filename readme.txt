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

* liststore.py - a list of lists structure with basic access and update methods,
  tracking changes to columns and rows, and column indexing for fast queries. 

* tablestore.py - a database/graph-like structure with Python types for columns,
  unique table keys, inter-table key reference integrity and a simple
  JSON save/load mechanism.

The overall development phase is maybe mid beta, excluding an envisioned asynchronous 
framework/mechanism based on asyncio, which may be at the slightly post pre-alpha stage.

Known compatibility is Python v3.9 and micropython v1.20-22.0, running on
the Raspberry Pi Pico and the Arduino Nano ESP 32.  I would like to support
newer versions of CircuitPython (8+), I haven't been able to get it all the
parts working yet.

To run a __name__=='__main__': style test script, start up a decent
terminal, change current directory to point to liststore and tablestore and run: 

python liststore.py

python tablestore.py

The big challenge is to reduce memory footprint for micro-controller platforms such
as the Raspberry Pi Pico and the Arduino Nano ESP 32, with 256KB and 512KB of "primary"
static RAM respectively, before allocating 80-100KB for heap memory.

On the Pico using gc.mem_free, the basic classes and functions ( at this point, May 2024 )
consume about 10KB ( after clearing import working memory with gc.collect ) at the start
of the test script.  The test scripts consume about 20-30KB total memory at the end of
the script. In a practical application, a TableStore or ListStore structure of a hundred
rows ( assuming 200 bytes per row ) might consume 40-50K. 

Still in beta, but it's moving along ... see https://github.com/billbreit/BitWiseApps/


     
