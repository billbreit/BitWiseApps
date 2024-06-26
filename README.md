### BitWiseApps

A toolkit for creating small footprint, high performance applications with Binary Logic on Python and MicroPython platforms.

The most significant modules so far are ListStore and TableStore which provide some level of database capability in a small memory footprint, a base of about 40K, usable on Raspberry Pi Pico and ESP32 microcontrollers.      

Current version is 0.4.2.

So far, I've added:

* A working version of bitlogic.py and bitslice.py, for debugging binary logic apps, performing bit surgery and as a compendium of bit logic algorithms and idioms.

* A mid(?) beta version of ListStore, a generic 'multi-list' structure illustrating binary logic techniques for compact, high-performance data structures.

* An early-mid beta version of TableStore implementing basic Python types, unique keys in tables, parent/child key relations between tables and persistent json storage.  TableStore is intended to provide something like minimal relational database functionality for MicroPython apps.

* A small demo of TableStore and DataStore using subclasses and class instances ... for The Raspberry Pi Zero Club !    

* a development version of VolatileDict (vdict), tracking changed values for pull notifications and providing more features than relatively slow OrderedDict.  Note: new Micropython versions seem to have much better dict performance than older versions ( pre-v20 ? ). 

* A small dev environment with prelimary performance data and experiemental stuff.  

See [Wiki Page](https://github.com/billbreit/BitWiseApps/wiki)
