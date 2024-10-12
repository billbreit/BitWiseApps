
import os, sys
import json

def is_micropython():
    return sys.implementation.name == 'micropython'
    
def path_seperator():
    if '\\' in os.getcwd():  
        return '\\'  # windows
    else:
        return '/'
        
def rel_parent_dir(path):
    pathsep = path_seperator()
    ppath = pathsep.join(path.split(pathsep)[:-1])
    return ppath

def fix_paths():
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


config_file_name = 'config.json'
config_file_path = rel_parent_dir(__file__) + path_seperator() + config_file_name


with open(config_file_path, "rt") as jfile:
    config_dict = json.load(jfile)

root_dir = config_dict['root_dir']  # expected root dir, if py, need to append sys.path 
local_dir = config_dict['local_dir']  # if mpy, may need to os.chdir
mpy_root = config_dict['mpy_root']       # mpy path defaults to ['', '.frozen', '/lib']
mpy_libs = config_dict['mpy_libs']
        
fix_paths()






