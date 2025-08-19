"""Mostly python/micropython compatiblity, testing """



import sys, os
import time
import json
from lib.core.fsutils import path_separator, rel_parent_dir

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

 
class JSONFileLoader:

    # defaults in subclass
    _def_dir = None
    _def_filename = None
    _def_extention = 'json'

    def __init__(self, fdir: str = None,
                       filename: str = None,
                       ext: str = None):

        self.default_dir = fdir or self._def_dir
        self.default_filename = filename or self._def_filename
        self.extention = ext or self._def_extention
        self.current_path = os.getcwd()
        self.parent_path = rel_parent_dir(os.getcwd())
        
        dir_path = path_separator().join([self.current_path,
                                          self.default_dir])

        print('--> try to make dir ', dir_path)
        try:
            os.mkdir(dir_path)
        except OSError:
            print('--> directory already exists')

    def make_filename(self, filename: str) -> str:
        """Construct filename, extention, path"""

        fname = filename or self.default_filename
        fname = '.'.join([fname, self.extention])
        if self.default_dir:
                fname =  path_separator().join([self.current_path,
                                                self.default_dir, fname])
        return fname

    def load( self, filename:str = None) -> dict:
        """Load a JSON file from _default_dir  """

        fname = self.make_filename(filename)
        with open( fname, "rt") as jfile:
            data = json.load(jfile)

        return data

    def save(self, data: dict, filename: str = None):
        """Save a JSON file from _default_dir"""

        fname = self.make_filename(filename)
        with open( fname, "wt") as jfile:
            json.dump(data, jfile)
