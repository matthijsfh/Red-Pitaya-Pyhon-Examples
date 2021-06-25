#==============================================================================
# Simple scope script using scpi interface to te RP.
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
from mpldatacursor import datacursor
import addcopyfighandler


def PreparePlot(Scope):
    fig = plt.figure()
    ax1 = plt.subplot(111)
    ax1.grid(True)
    ax1.set(ylabel='Volt [Volt]', xlabel='Time [msec]', title='Title')
    ax1.set_ylim([-20.0, 20.0])

    x = Scope.GetTimeVector() * 1000
   
    y1 = np.zeros((16384, 1))
    y2 = np.zeros((16384, 1))

    label_ch1 = ("Channel 1 (Probe %0.fx)" % + Scope.GetProbeGain(1))
    label_ch2 = ("Channel 2 (Probe %0.fx)" % + Scope.GetProbeGain(2))

    line1, = ax1.plot(x, y1, 'g-', label=label_ch1) # Returns a tuple of line objects, thus the comma
    line2, = ax1.plot(x, y2, 'b-', label=label_ch2) # Returns a tuple of line objects, thus the comma

    leg = ax1.legend();
   
    plt.tight_layout()
    plt.title('Simple Red Pitaya Scope')
    
    return fig, plt, line1, line2, ax1

def SetPlotYAxis(axis, YRange):
    Major = YRange / 10;
    Minor = YRange / 100;
    
    y_major_ticks = np.arange(-1 * YRange, YRange + Minor, Major)
    y_minor_ticks = np.arange(-1 * YRange, YRange + Minor, Minor)

    axis.set_yticks(y_major_ticks)
    axis.set_yticks(y_minor_ticks, minor=True)
    
    axis.set_ylim([-1 * YRange, YRange])

    return
    

def UpdatePlot(fig, line1, line2, Data1, Data2):
    line1.set_ydata(Data1)
    line2.set_ydata(Data2)
    
    fig.canvas.draw()
    fig.canvas.flush_events()
            
    return

def main():
    ip = "192.168.3.150"
    
    # create a scpi object.
    Pitaya = scpi.scpi(ip)
   
    # Create a scope object and set some defaults
    Scope = redpitaya_scope(Pitaya);     
    Scope.SetDecimation(2)    
    Scope.SetInputGain(Channel = 1, Gain = 'LV')
    Scope.SetInputGain(Channel = 2, Gain = 'LV')
    Scope.SetProbeGain(Probe = 1, Gain = 1)
    Scope.SetProbeGain(Probe = 2, Gain = 1)
    Scope.SetAverage(0)
    Scope.SetTrigger(Trigger = "CH1_PE", Level = 0, Delay = 8192)
    Scope.PrintSettings()

    [fig, plt, line1, line2, ax1] = PreparePlot(Scope)

    # Set plot axes based on probe scaling
    if (Scope.GetProbeGain(Probe = 1) == 10):
        SetPlotYAxis(ax1, 20)
    elif (Scope.GetProbeGain(Probe = 2) == 10):
        SetPlotYAxis(ax1, 20)
    else:
        SetPlotYAxis(ax1, 2)
        
    try:
        while True:
            Scope.Start()   
            # Timing with the scpi interface is not very good.
            # Add sleep(some number) if data seems not oke.
            # time.sleep(1)
        
            Scope.WaitForTrigger()
            # Timing with the scpi interface is not very good.
            # Add sleep(some number) if data seems not oke.
            # time.sleep(1)

            Data1 = Scope.GetGain(1) * Scope.GetData_Txt(Channel = 1)
            Data2 = Scope.GetGain(2) * Scope.GetData_Txt(Channel = 2)
            
            Pitaya.tx_txt('ACQ:STOP');

            UpdatePlot(fig, line1, line2, Data1, Data2)    
  
   
    except KeyboardInterrupt:
        print('interrupted!')
        Pitaya.close()
        datacursor(display="multiple", draggable=True)     
        plt.show()


if __name__== "__main__":
    main()