
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
    print('in rel_par_path: ', ppath)
    return ppath

print()
print('===== Entering dev.init subdirectory: dev.init.__init___ =====')
print()
print('In dev.init dir, os.getcwd ->', os.getcwd())
print()

# mpy, full path, crux of bootstrap problem
# this_dir = 'dev/init/'	
print('__init__.__file__ -> ', __file__)  # error if not defined

config_file_name = 'config.json'
config_file_path = rel_parent_dir(__file__) + path_seperator() + config_file_name
print('config path ', config_file_path)



"""
config_dict = { 'root_dir': 'bitwise',
                'local_dir': 'dev',
                'mpy_root': '/',
                'mpy_libs': ['ulib', 'dev']}

with open( config_file, "wt") as cfile:
    json.dump(config_dict, cfile)
"""

with open(config_file_path, "rt") as jfile:
    config_dict = json.load(jfile)
    
print('config_dict', config_dict)


root_dir = config_dict['root_dir']  # if py, need to append sys.path 
local_dir = config_dict['local_dir']  # if mpy, need to os.chdir
mpy_root = config_dict['mpy_root']       # mpy path defaults to ['', '.frozen', '/lib']
mpy_libs = config_dict['mpy_libs']

 


def fix_paths(libs:list=None):
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
    
    # need ismicropython
    # is there demo config vs. dev config ?
    
    print()
    print('=== Entering fix_path ')
    print()

    parent_dir = rel_parent_dir(os.getcwd())
    
    if not is_micropython():  # Python

        print('Python, add rel. parent to path ? ')
        print('rel. parent dir ', parent_dir)
 
        if parent_dir.endswith(root_dir):
            if parent_dir not in sys.path:   # assume python,
                print('par dir not in sys.path, appending parent dir ->', parent_dir)
                sys.path.append(parent_dir)
        else:
            parent_dir = os.getcwd()  # restore
            
    else:
        print('is micropython, par dir  ', parent_dir)
        print('cwd ', os.getcwd())
    print()

                      
    for slib in mpy_libs:  #micropython, or python with parent dir and not.
        subpath = parent_dir + path_seperator() + slib
        print('in subpath section ', subpath )
        if subpath not in sys.path:
            print('subpath not in sys.path, appending path ->',  slib)
            sys.path.append(subpath)
        print()
        
    print('=== Exiting fix_path ')
    
    return

"""
### Mess with cwd ?  In mpy production, setup.py and main.py will
    load from /, so better not.  May need context manager to save/restore cwd.

if is_micropython() :  # a biggy, cwd default is always '/'
    print('mpy -> os.pwd() ', os.getcwd())
    if os.getcwd()=='/':
        os.chdir(local_dir)
        print('os.pwd() ', os.getcwd())
    else:
        print('not micropython')
"""

print()

print('sys.path: ' , sys.path)
print()
        
fix_paths()

print()
print('fixed sys.path: ' , sys.path)
print()
print('=== Exiting dev.init.__init___')
print()




