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
import math
import random
from redpitaya_class import redpitaya_scope as redpitaya_scope
from redpitaya_class import redpitaya_generator as redpitaya_generator
from mpldatacursor import datacursor
import addcopyfighandler

cls = lambda: print("\033[2J\033[;H", end='')

def main():
    cls()
    
    ip = "192.168.3.150"
    
    # create a scpi object.
    Pitaya = scpi.scpi(ip)
   
    # Create a scope object and set some defaults
    Generator = redpitaya_generator(Pitaya);     
    # Generator.Sine(Channel = 1, Amplitude = 1, Frequency = 500)

    # Set frequency of generator to scopefreq/16384

    # Generator.Noise(Channel = 1, Amplitude = 1, Frequency = 30518.0 / 16384.0)
    # Generator.Noise(Channel = 1, Amplitude = 0.5, Frequency = 122070.0 / 16384.0)
    # Generator.Noise(Channel = 1, Amplitude = 1, Frequency = 61035.0 / 16384.0)
    
    Generator.ComplexDemo(Channel = 1, Amplitude = 1.0, Frequency = 100000 / 16384.0)
    
    Generator.EnableOutput(Channel = 1)
    Generator.PrintSettings()
    
    time.sleep(1)
    
    # Very important to close the scpi socket each time.
    Pitaya.close()
    

if __name__== "__main__":
    main()

