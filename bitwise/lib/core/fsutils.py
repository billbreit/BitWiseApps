# Warning: this code attempts to bridge between Python
# and micropython filesystems - it tends to be buggy.

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
    
    
# from fsinit.__init__
config_dict = { "local_dir": "tests",
                "mpy_root": "/",
                "mpy_libs": ["lib", "tests"],
                "root_dir": "bitwise"}
    
def fix_paths(libs:list=None):
    """Funky but necessary for mpy filesystem and relative-like imports.
       Note that:
       * micropython root ('') always in path.
       * For mpy v.20+, sys.path defaults ['', '.frozen', '/lib'].
       * getcwd() defaults '/', not literally in path, but works like
         blank '' anyway ( I think ). """
    
    import os, sys

    mpy_libs = libs or ['/lib', '/ulib', '/dev']
    
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
    
def new_fix_paths():
    """Fix Thyself.
    
       For mpy, add mpy_libs to '' path root.
       For Python, add parent if not in path.
         
       Funky but necessary for mpy filesystem with no relative imports. This 
       also facilitate easier peer-peer imports in full Python.  
       Note that:
       * micropython root ('') always in path.
       * For mpy v.20+, sys.path defaults ['', '.frozen', '/lib'].
       * getcwd() defaults '/', not literally in path, but works like
         blank '' anyway ( I think ). """
    
    import os, sys

    parent_dir = rel_parent_dir(os.getcwd())
    
    if is_micropython():  
        if mpy_root not in sys.path:   # assume python,
            sys.path.append(mpy_root) 
                
    else:    # Python
        if parent_dir.endswith(root_dir):
            if parent_dir not in sys.path:   # assume python,
                sys.path.append(parent_dir)
    # don't need, bad idea in mpy 
    # os.chdir(local_dir)
                      
    for slib in mpy_libs:  #micropython, or python with parent dir and not.
        subpath = parent_dir + path_seperator() + slib
        if subpath not in sys.path:
            sys.path.append(subpath)
 
    return
    
 
class JSONFileLoader:

    # defaults in subclass
    _def_dir = ''   # None
    _def_filename = '' #  None
    _def_extention = 'json'

    def __init__(self, fdir: str = None,
                       filename: str = None,
                       ext: str = None):

        self.default_dir = fdir or self._def_dir
        self.default_filename = filename or self._def_filename
        self.extention = ext or self._def_extention
        self.current_path = os.getcwd()
        self.parent_path = rel_parent_dir(os.getcwd())
        
        print('default_dir      ', self.default_dir )
        print('default_filename ', self.default_filename)
        print('extention        ', self.extention)
        print('current_path     ', self.current_path )
        print('parent_path ', self.parent_path )
        print('path_separator ', path_separator() )
        
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
        print('mf start fname ' , fname )
        print('mf current path', self.current_path)
        if self.default_dir:
            if is_micropython():
                if self.current_path == '/':
                    fname = '/' + self.default_dir + '/' + fname     
                else:
                    fname =  self.current_path.join([self.default_dir, fname])           
            else:
                

                fname =  path_separator().join([self.current_path,
                                              self.default_dir, fname])
            
        print('mf end fname ' , fname )
        return fname
        
    def save(self, data: dict, filename: str = None):
        """Save a JSON file from _default_dir"""
        
        data = self.prepare_types(data)

        fname = self.make_filename(filename)
        print('save fname ' , fname )
        with open( fname, "wt") as jfile:
            json.dump(data, jfile)
            

    def load( self, filename:str = None) -> dict:
        """Load a JSON file from _default_dir  """

        fname = self.make_filename(filename)
        print('load fname ' , fname )
        with open( fname, "rt") as jsfile:
            data = json.load(jsfile)
            
        data = self.restore_types(data)

        return data


    def prepare_types(self, json_dict:dict) -> dict:
        """Overidden in subclass"""
    
        return json_dict
    
    def restore_types(self, json_dict:dict) -> dict:
        """Overidden in subclass"""
    
        return json_dict


if __name__=='__main__':
    
    print('path sep ', path_separator())
    print()
    
    '''
    print('Running fix_paths ... ')
    print()
    print('sys.path before ', sys.path)
    print()
    fix_paths()
    print('sys.path after ', sys.path)
    print()
    '''
    
    from collections import OrderedDict as odict
    
    loadr = JSONFileLoader('mydata', 'myfile')
    
    dd = odict([( 'a', 1), ('b', 2), ('c',3)])
    
    loadr.save(dd)
    dd2 = loadr.load()
    
    # loadr.save(dd, 'newfile')
    # dd2 = loadr.load('newfile')
    
    print('dd2 ', dd2)


