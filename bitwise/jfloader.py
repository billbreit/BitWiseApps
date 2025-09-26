""" Debugging version of fsutils.JSONFileLoader"""

import os, sys
import json


def is_micropython():
    return sys.implementation.name == 'micropython'

from lib.core.fsutils import rel_parent_dir, path_separator


JFLDebug = False


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

        if JFLDebug:
            print('default_dir      ', self.default_dir )
            print('default_filename ', self.default_filename)
            print('extention        ', self.extention)
            print('current_path     ', self.current_path )
            print('parent_path ', self.parent_path )
            print('path_separator ', path_separator() )

        dir_path = path_separator().join([self.current_path,
                                          self.default_dir])

        if JFLDebug: print('--> try to make dir ', dir_path)
        try:
            os.mkdir(dir_path)
        except OSError:
            if JFLDebug: print('--> directory already exists')

    def make_filename(self, filename: str = None) -> str:
        """Construct filename, extention, path"""


        fname = filename or self.default_filename
        fname = '.'.join([fname, self.extention])
        if JFLDebug:
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

        if JFLDebug: print('mf end fname ' , fname )
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
        if JFLDebug: print('in load, fname: ' , fname )
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

    print('### Testing / Debug JSONFileLoader ### \n')
    print('path separator: ', path_separator())
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
    fdata = ('mydata', 'myfile' )
    from collections import OrderedDict as odict
    
    JFLDebug = True

    loadr = JSONFileLoader(*fdata)

    dd = odict([( 'a', 1), ('b', 2), ('c',3)])
    print('dd dict OrderCollection, note restored order on mpy. \n')
    print(dd)
    print()
    
    print('save/restore using ', fdata ) 

    loadr.save(dd)
    dd2 = loadr.load()
    
    print('restored dd2 ', dd2)
    
    print("save/restore using 'newfile'" ) 

    loadr.save(dd, 'newfile')
    dd3 = loadr.load('newfile')

    print('dd3 ', dd3)


