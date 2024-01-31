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
    """Fix for mpy filesystem and relative-like imports.
       Note that:
       * micropython root ('') always in path.
       * getcwd always '/' no matter what and not literally in path,
         but works like blank '' anyway ( I think ). """
    
    import os, sys

    libs = ['/dev', '/ulib']
    
    # print('starting fix_paths')

    # print('path before ', sys.path)
    # print('getcwd ', os.getcwd())

    p = os.getcwd()

    if '\\' in p:
        parse = '\\'  # windows
        # print('windows')
    else:
        parse = '/'  # linux
        # print('linux')

    parentdir = parse.join(p.split(parse)[:-1])      
    
    # print('parentdir ', parentdir)
    
    if parentdir not in sys.path:   # python,
        sys.path.append(parentdir)
        # print('path after in append parentdir ', sys.path)
        # print('in append parentdir, supposedly returning')
        return
                          
    for l in libs:  #micropython
        if parentdir+l not in sys.path:
            # print('in append parentdir+l')
            sys.path.append(parentdir + l)

    # print('path after ', sys.path)
    # print('end')
    
    return





