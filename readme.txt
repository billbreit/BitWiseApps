

README.txt for Bill Breitmayer's hello-world, a temporary project
to help me learn about GitHub projects.  My focal areas are:

- Binary Logic applications

- Cross-Python libraries, including core Python and micropython, and
  when possible Circuit Python, or any other worthy Python dialect.

The first example is BitLogic, a ones-complement wrapper in a 
two-complement world - for debugging, not deployment.  It may provide
a foundation for developing what I call "binary logic applications".

The development phase is maybe early beta.

Known compatibility is Python v3.9 and micropython v1.20.0, running on
a Pico.  Not sure about CircuitPython, I haven't been able to get it
working yet.

To run a __name__=='__main__': style test script, start up a decent
terminal, change current directory to point to bitlogic.py and run: 

python bitlogic.py

On the Pico using gc.mem_free, the basic classes and functions consume
about 1.6K ( to the start of the test script ) .  The entire test script
consumes about 20K ( total memory at the end of the script).

 

https://gitgub.com/billbreit/hello-world

     
