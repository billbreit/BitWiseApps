### BitWiseApps

A toolkit for creating small footprint, high performance applications with Binary Logic on Python and MicroPython platforms. 

So far, I've added:

* a working version of bitlogic.py, for debugging binary logic apps and as a compendium of bit logic algorithms and idioms.

* an early beta version of ListStore, a generic 'multi-list' structure illustrating binary logic techniques for compact, high-performance data structures.  Eventually, ListStore will implement persistent json storage and pave the way to TableStore and something like a minimal relational database for MicroPython apps.   

* a development version of VolatileDict (vdict), tracking changed values for pull notifications and providing more features than relatively slow OrderedDict.  Note: new Micropython versions seem to have much better dict performance than older versions ( pre-v20 ? ). 

* A small dev environment with prelimary performance data and experiemental stuff.  

See [Wiki Page](https://github.com/billbreit/BitWiseApps/wiki)
