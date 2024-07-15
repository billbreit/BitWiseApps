
import os, sys

print('In ulib.test1 ...')

print('os.getcwd() ', os.getcwd())
print('sys.path ', sys.path)

def greetings(whomever='whomever'):
    
    return 'Greetings ' + whomever

print('Exiting ulib.test1 ...')