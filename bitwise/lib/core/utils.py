"""Mostly python/micropython compatiblity, testing """



import sys, os
import time
import json
# from lib.core.fsutils import path_separator, rel_parent_dir

def ismicropython():
    
    return sys.implementation.name == 'micropython'
    
def timer(func, repeat=1): 
    """This function shows the execution time of the function object passed."""
    # Repeat doesn't work ( or make sense ) for @timer(repeat=123), only as call.
   
    scale_msec = 1000000
    
    def wrapped_func(*args, **kwargs): 
        t1 = time.time_ns()
        for _ in range(repeat):
            result = func(*args, **kwargs) 
        t2 = time.time_ns() 
        print(f'Timed {func.__name__!r} repeated {repeat} times: {(t2-t1)/scale_msec} msecs.') 
        return result
         
    return wrapped_func

