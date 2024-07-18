

import os, sys


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

