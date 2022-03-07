#==============================================================================
# Simple signal generator script using scpi interface to te RP.
# Not very fast, but enough to check if there is data and 
# for example the signal generator is running
#
# M. Hajer, 2021
#==============================================================================

import sys
sys.path.append('../classes')

import os
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import numpy as np
from redpitaya_class import redpitaya_scope as redpitaya_scope
from redpitaya_class import redpitaya_generator as redpitaya_generator
from mpldatacursor import datacursor
import addcopyfighandler


def main():
    ip = "192.168.3.150"
    
    # create a scpi object.
    Pitaya = scpi.scpi(ip)
   
    # Create a scope object and set some defaults
    Generator = redpitaya_generator(Pitaya);     
    # Generator.Sine(Channel = 1, Amplitude = 1, Frequency = 500)
    Generator.Square(Channel = 1, Amplitude = 0.5, Frequency = 10)
    Generator.EnableOutput(Channel = 1)

    # Generator.Square(Channel = 2, Amplitude = 0.5, Frequency = 2000)
    # Generator.EnableOutput(Channel = 2)
    # Generator.EnableBothOutputs()

    
    # Very important to close the scpi socket each time.
    Pitaya.close()
    

if __name__== "__main__":
    main()

