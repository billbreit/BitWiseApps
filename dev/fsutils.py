""" Fiddly bits for fs compatibility
    Three distinct file system environments:
    * Python/Linux
    * Python/Windows
    * MicroPython on a micro-controller ( rp2 or eps32 )
    
    MPy 20+ starts with sys.path -> ['', '.frozen', '/lib'].
    
    os.getcwd() = '/', no matter what directory the program
    is running from.
    
    os.chdir('/dev'), os.getcwd() -> '/dev'
    
"""
try:
    from utils import fix_paths
except:
    from dev.utils import fix_paths

import os
import sys

print('Running fix_paths ... ')
print()
print('sys.path before ', sys.path)
print()
fix_paths()
print('sys.path after ', sys.path)
print()

from collections import namedtuple


StatResult_fields = ['st_mode', 'st_ino', 'st_dev', 'st_nlink', 'st_uid', 'st_gid',
                                                   'st_size', 'st_atime', 'st_mtime', 'st_ctime' ]

StatResult = namedtuple('StatResult', StatResult_fields )  

# Mostly from mpy pathlib.py.  Python module stat.py has masks 

def isdir(path:str) -> bool:
    try:
       # mode = os.stat(path)[0]
        return bool(os.stat(path)[0] & 0o040000)
    except OSError:
        return False


def isfile(path:str) -> bool:
    try:
        # return bool(os.stat(path)[0] & 0x8000)
        # mode = os.stat(path)[0]
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



if __name__=='__main__':
        
    print('path separator', path_separator() )
    
    print("stat '/' -> ", StatResult(*os.stat('/')))
    print()
    try:
        print(f"os.stat({path}) ", os.stat(path))
    except Exception as e:
        print(e)

    p = '/'
    print("exists('/') ", path_exists(p))
    print("isfile('/') ", isfile(p))
    print("isdir('/') ", isdir(p))
    print("bin (stat '/').st_mode ", bin(StatResult(*os.stat('/')).st_mode))
    print("oct (stat '/').st_mode ", oct(StatResult(*os.stat('/')).st_mode))
    print("hex (stat '/').st_mode ", hex(StatResult(*os.stat('/')).st_mode))
    print()
    
    path = None
    for p in ['bitlogic.py', 'dev/bitlogic.py']:
        if path_exists(p):
            print(p, ' exists')
            path = p
        else:
            print(p , 'not exists ') 

    print()
    print(f"exists('{path}')", path_exists(path))
    print(f"isfile('{path}' ", isfile(path))
    print(f"isdir('{path}' ", isdir(path))
    print(f"bin (stat '{path}').st_mode ", bin(StatResult(*os.stat(path)).st_mode))
    print(f"oct (stat '{path}').st_mode ", oct(StatResult(*os.stat(path)).st_mode))
    print(f"hex (stat '{path}').st_mode ", hex(StatResult(*os.stat(path)).st_mode))
    print()
    
    """
        for tt in [bin, oct, hex ]:
                print('str tt ', str(tt))
                print(f" stat '/home/billb/Projects'    ",  tt(StatResult(*os.stat('/home/billb/Projects')).st_mode))
        
        for tt in [bin, oct, hex ]:
                print(f"{str(tt)} stat 'bitlogic.py'    ",  tt(StatResult(*os.stat('bitlogic.py')).st_mode))
    """

    print("exists '/rrr' )", path_exists('/rrr'))
    print("exists 'xxx' )", path_exists('xxx'))
    

