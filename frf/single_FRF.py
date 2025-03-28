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
import addcopyfighandler
import mplcursors

from scipy.fft import fft

from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

cls = lambda: print("\033[2J\033[;H", end='')

def PreparePlot(Scope):
    fig = plt.figure()
    ax1 = plt.subplot(111)
    ax1.grid(True)
    ax1.set(ylabel='Volt [Volt]', xlabel='Time [msec]', title='Title')
    ax1.set_ylim([-20.0, 20.0])

    x = Scope.GetTimeVector() * 1000
    x_trig = Scope.GetTriggerVector() * 1000
    
    y_trig = np.array([-1.0 , 1.0]) * 20.0
   
    y1 = np.zeros((16384, 1))
    y2 = np.zeros((16384, 1))

    label_ch1 = ("Channel 1 (Probe %0.fx)" % + Scope.GetProbeGain(1))
    label_ch2 = ("Channel 2 (Probe %0.fx)" % + Scope.GetProbeGain(2))
    label_trig = ("Trigger position")

    line1,       = ax1.plot(x, y1, 'g-', label=label_ch1) # Returns a tuple of line objects, thus the comma
    line2,       = ax1.plot(x, y2, 'b-', label=label_ch2) # Returns a tuple of line objects, thus the comma
    triggerline, = ax1.plot(x_trig, y_trig, 'r-') 

    leg = ax1.legend();
   
    plt.tight_layout()
    plt.title('Red Pitaya Scope')
    
    return fig, plt, line1, line2, triggerline, ax1


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
    cls()
    
    ip = "192.168.3.150"
    
    # create a scpi object.
    Pitaya = scpi.scpi(ip)
   
    # Create a scope object and set some defaults
    Scope = redpitaya_scope(Pitaya);     
    # Scope.SetDecimationBeta(13)    
    Scope.SetDecimationBeta(11)    
    Scope.SetInputGain(Channel = 1, Gain = 'LV')
    Scope.SetInputGain(Channel = 2, Gain = 'LV')
    Scope.SetProbeGain(Probe = 1, Gain = 1)
    Scope.SetProbeGain(Probe = 2, Gain = 1)
    Scope.SetAverage(0)
    Scope.SetTrigger(Trigger = "NOW")
       
    try:
        # while True:
        Scope.SetTrigger(Trigger = "DISABLED")
        Scope.Start()   

        time.sleep(1)

        Scope.SetTrigger(Trigger = "CH1_PE", Level = 0.5, Delay = 8192)
        Scope.PrintSettings()
        Scope.WaitForTrigger()

        [fig, plt, line1, line2, triggerline, ax1] = PreparePlot(Scope)
    
        # Set plot axes based on probe scaling
        if (Scope.GetProbeGain(Probe = 1) == 10):
            SetPlotYAxis(ax1, 20)
        elif (Scope.GetProbeGain(Probe = 2) == 10):
            SetPlotYAxis(ax1, 20)
        else:
            SetPlotYAxis(ax1, 2)

        # Timing with the scpi interface is not very good.
        # Add sleep(some number) if data seems not oke.
        # Make sure to wait long enoug for the measurement to finish.
        time.sleep(1)

        Data1 = Scope.GetGain(1) * Scope.GetData_Txt(Channel = 1)
        Data2 = Scope.GetGain(2) * Scope.GetData_Txt(Channel = 2)
        
        # Pitaya.tx_txt('ACQ:STOP');

        print("Delay : %.6f Sec"  % ((8192-0)/Scope.Frequency))
        UpdatePlot(fig, line1, line2, Data1, Data2)    
   
    except KeyboardInterrupt:
        print('interrupted!')
        
    Pitaya.close()
    # mplcursors.cursor([ax1], multiple=True)



    if(1):
        x = np.arange(0, 16384)

        G = fft(Data1) / fft(Data2)
        length = len(G)
        middle_index = length//2

        freq = x[:middle_index] / 16384 * Scope.Frequency
        H = G[:middle_index]

        db_mag = 20 * np.log10(np.abs(H))
        phase = np.arctan2(np.imag(H), np.real(H)) * 180/np.pi

        # fig = plt.figure()

        # ax11 = plt.subplot(211)
        # plt.semilogx(freq, db_mag)
        # ax11.grid(which="both")
        # ax11.set(ylabel='Gain [dB]', xlabel='Frequency [Hz]', title='Bode plot')
        # ml = MultipleLocator(1)
        # ax12.yaxis.set_minor_locator(ml)
        # ax12.grid(which='minor', alpha=0.3)
        # ax12.grid(which='major', alpha=1.0)
        
        # ax12 = plt.subplot(212)
        # plt.semilogx(freq, phase)
        # ax12.grid(which="both")
        


        fig = plt.figure()
        plt.minorticks_on()
    
        ax21 = plt.subplot(211)
        ax21.grid(which="both")
        plt.semilogx(freq, db_mag, 'b-')
        plt.minorticks_on()
        ax21.grid(which='minor', alpha=0.3)
        ax21.grid(which='major', alpha=1.0)
    
        # Fix the minor grid lines on the upper Y-axis
        # 1 dB on gain plot.
        ml = MultipleLocator(1)
        ax21.yaxis.set_minor_locator(ml)
        ax21.grid(which='minor', alpha=0.3)
        ax21.grid(which='major', alpha=1.0)
        ax21.set(ylabel='Gain [dB]', xlabel='Frequency [Hz]', title='Bode plot')
    
    
        ax22 = plt.subplot(212)
        ax22.grid(which="both")
        plt.semilogx(freq, phase, 'b-')
        plt.minorticks_on()
    
        # Fix the minor grid lines on the lower Y-axis
        # 10 degree on phase plot
        ml = MultipleLocator(10)
        ax22.yaxis.set_minor_locator(ml)
        ax22.grid(which='minor', alpha=0.3)
        ax22.grid(which='major', alpha=1.0)
        ax22.set(ylabel='Phase [deg]', xlabel='Frequency [Hz]')
        
        

    mplcursors.cursor([ax21, ax22], multiple=True)

    plt.show()


if __name__== "__main__":
    main()