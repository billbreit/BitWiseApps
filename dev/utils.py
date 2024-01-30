"""Development/debug utils """

import time
from random import randint

scale_msec = 1000000
 
  
def timer(func, repeat=1): 
    """This function shows the execution time of the function object passed."""
    # Repeat doesn't work ( or make sense ) for @timer(repeat=123), only as call.
    
    def wrapped_func(*args, **kwargs): 
        t1 = time.time_ns()
        for _ in range(repeat):
            result = func(*args, **kwargs) 
        t2 = time.time_ns() 
        print(f'Timed {func.__name__!r} repeated {repeat} times: {(t2-t1)/scale_msec} msecs.') 
        return result
         
    return wrapped_func
    
    
def genrandint(size):
    """ Overcome 2**30 barrier in mpy, size is base 2 exponent.  Numbers are probably
        more arbitrary than random. Use for performance testing only."""
   
    dvd, man = divmod(size, 30)
    rint = 0
 
    for d in range(dvd):
        rint|= rint<<30 | randint(0, 2**30)
        
    if man > 0:
        rint|= rint<<man | randint(0, 2**man)
        
    return rint  

    
def fix_paths():
    """Fix for mpy filesystem and relative imports, os.pwd() always '/'. """
    
    import os, sys

    libs = ['/dev', '/ulib']

    # print('path before ', sys.path)
    # print('pwd ', os.getcwd())

    p = os.getcwd()

    parentdir = ('/'.join(p.split('/')[:-1]))
    # print('parentdir ', parentdir)
    
    if parentdir not in sys.path:   # python
        sys.path.append(parentdir)
    else:                           #micropython
        for l in libs:
            if l not in sys.path:
                sys.path.append(parentdir + l)

    # print('path after ', sys.path)





