

import os


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

