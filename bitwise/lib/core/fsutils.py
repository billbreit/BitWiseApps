

import os, sys
import json


def is_micropython():
    return sys.implementation.name == 'micropython'

def isdir(path:str) -> bool:
    try:
        return bool(os.stat(path)[0] & 0o040000)
    except OSError:
        return False

def isfile(path:str) -> bool:
    try:
        return bool(os.stat(path)[0] & 0o100000)
    except OSError:
        return False
                
def path_exists(path:str) -> bool:
    try:
        os.stat(path)
        return True
    except OSError:
        return False

def path_separator() -> str:
    """ Dumb, but should be reliable"""

    if '\\' in os.getcwd():
        return '\\'  # windows
    else:
        return '/'  # linux py or mpy
        
def rel_parent_dir(path):
    pathsep = path_separator()
    ppath = pathsep.join(path.split(pathsep)[:-1])
    
    return ppath
    
def fix_paths(libs:list=None):
    """Funky but necessary for mpy filesystem and relative-like imports.
       Note that:
       * micropython root ('') always in path.
       * For mpy v.20+, sys.path defaults ['', '.frozen', '/lib'].
       * getcwd() defaults '/', not literally in path, but works like
         blank '' anyway ( I think ). """
    
    import os, sys

    mpy_libs = libs or ['/ulib', '/dev']
    
    p = os.getcwd()

    
    pathsep = path_separator()
    parentdir = pathsep.join(p.split(pathsep)[:-1])      
 
    if parentdir not in sys.path:   # python,
        sys.path.append(parentdir)
        return
                          
    for l in mpy_libs:  #micropython, no rel. import so ..
        if parentdir+l not in sys.path:
            sys.path.append(parentdir + l)
    
    return
    
 
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

    def make_filename(self, filename: str = None) -> str:
        """Construct filename, extention, path"""

        fname = filename or self.default_filename
        fname = '.'.join([fname, self.extention])
        if self.default_dir:
                fname =  path_separator().join([self.current_path,
                                                self.default_dir, fname])
        return fname
        
    def save(self, data: dict, filename: str = None):
        """Save a JSON file from _default_dir"""
        
        data = self.prepare_types(data)

        fname = self.make_filename(filename)
        with open( fname, "wt") as jfile:
            json.dump(data, jfile)
            

    def load( self, filename:str = None) -> dict:
        """Load a JSON file from _default_dir  """

        fname = self.make_filename(filename)
        with open( fname, "rt") as jfile:
            data = json.load(jfile)
            
        data = self.restore_types(data)

        return data


    def prepare_types(self, json_dict:dict) -> dict:
        """Overriden in subclass"""
    
        return json_dict
    
    def restore_types(self, json_dict:dict) -> dict:
        """Overriden in subclass"""
    
        return json_dict


if __name__=='__main__':
    
    print('path sep ', path_separator())
    print()
    
    print('Running fix_paths ... ')
    print()
    print('sys.path before ', sys.path)
    print()
    fix_paths()
    print('sys.path after ', sys.path)
    print()

