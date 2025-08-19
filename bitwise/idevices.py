
"""Imaginary Devices"""

from random import random

class Fan(object):

    OFF:int = 0
    ON:int  = 1

    def __init__(self, *args, **kwargs):

        self.state:int = self.OFF

    def set_state(self, new_state:int, verbose:bool=False ):
    
        if verbose:
            if new_state == self.OFF:
                print('Fan -> Turning fan OFF')
            elif new_state == self.ON:
                print('Fan -> Turning fan ON')
            else:
                print('Fan -> Unknown fan state: ', new_state)
 
        self.state = new_state

    def get_state(self):

        return self.state
        
class RandomThermometer(object):
    """"The most boring of all devices, spiced up a bit.
        
        |------------------------------------|
                         |
                        mid
        < ---          range             --- >
                       vari            
    
    mid:float=21.0
    range:float=4.0
    variability:float=5.0, can be negative
    
    """
    
    def __init__(self, mid:float=21.0, trange:float=4.0, vari:float=5.0):
    
        self.mid = mid
        self.range = trange
        self.variability = vari 

    def read(self):
    
        return round(self.mid + ( self.range - self.variability*random()),2)
        

class LED(object):

    RED:tuple   = ( 255, 0, 0 )
    GREEN:tuple = ( 0, 255, 0 )
    BLUE:tuple  = ( 0, 0, 255 )
    WHITE:tuple = ( 255, 255, 255 )
    OFF:float   = 0.0    #  0.0 -> 1.0
    ON:float    = 1.0

    def __init__(self, *args, **kwargs):

        self.color:tuple = self.RED
        self.brightness:float = self.ON

    def set(self, color:tuple=None, brightness:float=None):
        """Dual purpose function- color() and brightness()."""

        if color:
            self.color = color
        if brightness is not None:  # could be 0.0
            self.brightness  = brightness

    @property
    def get_state(self):

        return ( self.color, self.brightness )

class Thermostat(object):


    def __init__(self, *args, **kwargs):
    
        self.setting = 35
        
    def get_setting(self):
    
        return self.setting 
        
    def reset(self, temp:float ):
    
        self.setting = temp
        

class Switch(object):

    OFF:int = 0
    ON:int  = 1

    def __init__(self, *args, **kwargs):

        self.state = self.OFF

    def set_state(self, new_state:int ):

        self.state = new_state

    def get_state(self):

        return self.state

