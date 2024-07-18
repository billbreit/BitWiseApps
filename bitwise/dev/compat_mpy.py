"""Mostly for Python/micropython compatibility"""

print('in dev __init__')


__all__ = ['const']

try:
    from micropython import const 
except:
    const = lambda x : x
    


