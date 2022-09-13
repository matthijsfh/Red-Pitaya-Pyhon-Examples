import sys
import time
import redpitaya_scpi as scpi
import numpy as np
import math
import random

# https://github.com/RedPitaya/RedPitaya/blob/master/scpi-server/src/scpi-commands.c#L96-L204
# <source> = {DISABLED, NOW, CH1_PE, CH1_NE, CH2_PE, CH2_NE, EXT_PE, EXT_NE, AWG_PE, AWG_NE} Default: DISABLED
# <status> = {WAIT, TD}
# <time> = {value in ns}
# <counetr> = {value in samples}
# <gain> = {LV, HV}
# <level> = {value in V}
# <mode> = {AC,DC}

#==============================================================================
# Scope class
#==============================================================================
class redpitaya_scope:
    rp = []
    NrSamples             = int(16384)
    Decimation            = 1;
    Frequency             = 125e6/(Decimation * NrSamples)
    SampleFrequency       = 125e6
    Duration              = (Decimation * NrSamples) / SampleFrequency
    Gain                  = np.array([1, 1])
    Probe                 = np.array([1, 1])
    TriggerDelay          = 0
    Decimation_Array      = np.array([1, 8, 64, 1024, 8192, 65536])
    Decimation_Array_Beta = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536])
    Average               = 0;
    
    def __init__(self, pitaya):
        self.rp = pitaya
        self.rp.tx_txt('ACQ:DATA:FORMAT ASCII')
        self.rp.tx_txt('ACQ:RST')
        self.rp.tx_txt('ACQ:START')
        return
    
    def Start(self):
        self.rp.tx_txt('ACQ:RST')
        self.rp.tx_txt('ACQ:DATA:FORMAT ASCII')
        self.WriteDecimation()
        self.WriteTrigger()
        self.rp.tx_txt('ACQ:START')
        self.rp.tx_txt('DIG:PIN LED0, 1')
        return

    def WaitForTrigger(self):
        while 1:
            self.rp.tx_txt('ACQ:TRIG:STAT?')
        
            answer = self.rp.rx_txt()
            print(answer)
        
            if 'TD' in answer:
                break
        
        # make sure the data is ready
        # to do: especially on slow measurements.
        time.sleep(0.1)
        self.rp.tx_txt('DIG:PIN LED0, 0')
        # self.rp.tx_txt('ACQ:STOP')
       
        return

    def Stop(self):
         self.rp.tx_txt('ACQ:STOP')
         return
    
    def GetData_Txt(self, Channel = 1):
        
        if (Channel == 1):
            self.rp.tx_txt('ACQ:SOUR1:DATA?')
        else:
            self.rp.tx_txt('ACQ:SOUR2:DATA?')
            
        buff_string = self.rp.rx_txt()
        buff_string = buff_string.strip('{}\n\r')
        return np.fromstring(buff_string, sep=',')
        
    #==============================================================================
    # Nov-2021: Not all decimations do work in the stable release of the red pitaya. 
    # This is error in the documentation on the website.
    # I have tested and only: {1,8,64,1024,8192,65536} do work.
    # Confirmed by old pdf manual of RP.
    #==============================================================================
    def SetDecimation(self, Decimation_Index):
        if (Decimation_Index >= 6):
            print("Error decimation not valid!")
            self.Decimation = 1;
        else:
            self.Decimation = self.Decimation_Array[Decimation_Index];

        self.Frequency = 125e6/(self.Decimation)
        self.Duration  = (self.Decimation * self.NrSamples) / self.SampleFrequency
        self.WriteDecimation()
        return
    
    #==============================================================================
    # NOv-2021
    # Starting from version 1.04-9 (BETA) the full list of decimations is available
    # 1,2,4,8,16,32,64,128,256,1024,2048,4096,8192,16384,32768,65536 
    #==============================================================================
    def SetDecimationBeta(self, Decimation_Index):
        if (Decimation_Index >= np.size(self.Decimation_Array_Beta)):
            print("Error decimation not valid!")
            self.Decimation = 1;
        else:
            self.Decimation = self.Decimation_Array_Beta[Decimation_Index];

        self.Frequency = 125e6/(self.Decimation)
        self.Duration  = (self.Decimation * self.NrSamples) / self.SampleFrequency
        self.WriteDecimation()
        return

    def WriteDecimation(self):
        self.rp.tx_txt('ACQ:DEC ' + str(self.Decimation) )
        return
    
    #==============================================================================
    # Options are: 
    # {DISABLED, NOW, CH1_PE, CH1_NE, CH2_PE, CH2_NE, EXT_PE, EXT_NE, AWG_PE, AWG_NE}
    # Delay will shift the plot. 
    # 8192 will restult in triggered value as first sample of the data.
    # 0 will result in triggered value as mid point of the data
    # -8192 will result in triggered value as last point of the data
    #==============================================================================
    def SetTrigger(self, Trigger = 'CH1_PE', Level = 0, Delay = 8192):
        self.TriggerConf = Trigger
        self.TriggerLevel = Level
        self.TriggerDelay = Delay
        
        self.WriteTrigger()
        return
    
    def WriteTrigger(self):
        self.rp.tx_txt('ACQ:TRIG ' + self.TriggerConf )        
        self.rp.tx_txt('ACQ:TRIG:DLY ' + str(self.TriggerDelay) )
        self.rp.tx_txt('ACQ:TRIG:LEV ' + str(self.TriggerLevel) )
        return
    
    #==============================================================================
    # Averaging
    #==============================================================================
    def SetAverage(self, Average = 0):
        self.Average = Average
      
        self.WriteAverage()
        return
    
    def WriteAverage(self):
        self.rp.tx_txt('ACQ:AVG ' + str(self.Average))        
        return


    def PrintSettings(self):
        print("Decimation      : %d"  % (self.Decimation))

        if (self.Frequency > 1e6):
            print("Frequency       : %.3f MHz"  % (self.Frequency/1e6))
        elif (self.Frequency > 1e3):
            print("Frequency       : %.3f kHz"  % (self.Frequency/1e3))
        else:
            print("Frequency       : %.3f Hz"  % (self.Frequency))
        
        if (self.Duration < 1e-3):
            print("Duration        : %.3f usec"  % (self.Duration*1e6))
        elif (self.Duration < 1):
            print("Duration        : %.3f msec"  % (self.Duration*1e3))
        else:
            print("Duration        : %.3f sec"  % (self.Duration))
            
        print("Trigger         : " + self.TriggerConf)
        print("Trigger Delay   : %d samples" % (self.TriggerDelay))
        print("Trigger Level   : %.3f Volt (on ADC level)" % (self.TriggerLevel))
        print("Range 1         : +/-%.1f Volt" % self.Gain[0])
        print("Range 2         : +/-%.1f Volt" % self.Gain[1])
        print("Probe 1         : %.0fx" % self.Probe[0])
        print("Probe 2         : %.0fx" % self.Probe[1])
        return;

    def GetTimeVector(self):
        TimeVector = np.arange(self.NrSamples) / self.Frequency
        return TimeVector
    
    def GetDuration(self):
        return self.Duration
    
    #==============================================================================
    # Return the location of the trigger in the data. 
    # Used in the plot to show the trigger location.
    #==============================================================================
    def GetTriggerVector(self):
        TriggerVector = np.ones((2,1)) * ((self.NrSamples/2) - self.TriggerDelay) / self.Frequency
        return TriggerVector

    def GetTriggerData(self):
        TriggerData = np.array([-1.0 , 1.0]) * 2.0
        
        if (self.Gain[0] == 10) or (self.Gain[1] == 10):
            TriggerData = TriggerData * 10
        
        if (self.Probe[0] == 10) or (self.Probe[1] == 10):
            TriggerData = TriggerData * 10

        return TriggerData
    

    def SetInputGain(self, Channel = 1, Gain='LV'):
        if (Channel == 1):
            if 'LV' in Gain:
                self.Gain[0] = 1
                self.rp.tx_txt('ACQ:SOUR1:GAIN LV')
            else:
                self.Gain[0] = 10
                self.rp.tx_txt('ACQ:SOUR1:GAIN HV')

        if (Channel == 2):
            if 'LV' in Gain:
                self.Gain[1] = 1
                self.rp.tx_txt('ACQ:SOUR2:GAIN LV')
            else:
                self.Gain[1] = 10
                self.rp.tx_txt('ACQ:SOUR2:GAIN HV')
        return
    
    def SetProbeGain(self, Probe=1, Gain=1):
        if (Probe == 1):
            self.Probe[0] = Gain
        else:
            self.Probe[1] = Gain

        return

    def GetProbeGain(self, Probe=1):
        if (Probe == 1):
            return self.Probe[0]
        else:
            return self.Probe[1]

    def GetGain(self, Channel=1):
        Gain = self.Probe[Channel-1] * self.Gain[Channel-1]
        return Gain
    
    
    def GetYRange(self):
        Range = 2
        if (self.Gain[0] == 10) or (self.Gain[1] == 10):
            Range = Range * 10
    
        if (self.Probe[0] == 10) or (self.Probe[1] == 10):
            Range = Range * 10
        
        return Range


#==============================================================================
# Signal generator class
#==============================================================================
class redpitaya_generator:
    rp                  = []
    NrSamples           = int(16384)
    GenSignalType       = np.array([0.0, 0.0])
    Amplitude           = np.array([1.0, 1.0])
    Frequency           = np.array([100.0, 100.0])

    # {SINE, SQUARE, TRIANGLE, SAWU, SAWD, PWM, ARBITRARY, DC, DC_NEG}

    def __init__(self, pitaya):
        self.rp = pitaya
        return

    #==============================================================================
    # Sine wave
    #==============================================================================
    def Sine(self, Channel = 1, Amplitude = 1.0, Frequency = 100.0):
        self.GenSignalType[Channel - 1] = 0
        self.Amplitude[Channel - 1] = Amplitude
        self.Frequency[Channel - 1] = Frequency
        self.ConfigureSignalGen(Channel)
        return
        
    #==============================================================================
    # Square wave
    #==============================================================================
    def Square(self, Channel = 1, Amplitude = 1.0, Frequency = 100.0):
        self.GenSignalType[Channel - 1] = 1
        self.Amplitude[Channel - 1] = Amplitude
        self.Frequency[Channel - 1] = Frequency
        self.ConfigureSignalGen(Channel)
        return
        
    #==============================================================================
    # Noise wave (ARBITRARY)
    #==============================================================================
    def Noise(self, Channel = 1, Amplitude = 1.0, Frequency = 100.0):

        # Frequency for the entire buffer.
        self.GenSignalType[Channel - 1] = 6
        self.Amplitude[Channel - 1] = Amplitude
        self.Frequency[Channel - 1] = Frequency
        
        BUFF_SIZE = 16384
        z = ''
        
        for i in range(0, BUFF_SIZE-2):
            z += str(2.0 * random.random() - 1.0) + ', '

        z += str(2.0 * random.random() - 1.0)

        # last sample without "," after it.
        if (Channel == 1):
            self.rp.tx_txt('SOUR1:TRAC:DATA:DATA ' + z)

        if (Channel == 2):
            self.rp.tx_txt('SOUR2:TRAC:DATA:DATA ' + z)
        
        self.ConfigureSignalGen(Channel)

        return    
    
    #==============================================================================
    # Noise wave (ARBITRARY)
    #==============================================================================
    def ComplexDemo(self, Channel = 1, Amplitude = 1.0, Frequency = 100.0):

        # Frequency for the entire buffer.
        self.GenSignalType[Channel - 1] = 6
        self.Amplitude[Channel - 1] = Amplitude
        self.Frequency[Channel - 1] = Frequency
        
        BUFF_SIZE = 16384
        
        y = ''
        x = ''
        t = []
        
        for i in range(0, BUFF_SIZE):
            t.append((2 * math.pi) / BUFF_SIZE * i)
        
        for i in range(0, BUFF_SIZE-1):
            if(i != BUFF_SIZE-2):
                b = math.sin(t[i]) + (1.0/3.0) + math.sin(t[i] * 3)
    
                if(b <= -1 or b >= 1):
                    x += str(-1.0) + ', '
                    y += str(-1.0) + ', '
                else:
                    x += str(math.sin(t[i]) + (1.0/3.0) + math.sin(t[i] * 3)) + ', '
                    y += str((1.0 / 2.0) * math.sin(t[i]) + (1.0/4.0) * math.sin(t[i] * 4)) + ', '
                    
            else:
                c = math.sin(t[i]) + (1.0/3.0) + math.sin(t[i] * 3)
                if(c <= -1 or c >= 1):
                    x += str(-1.0)
                    y += str(-1.0)
                else:
                    x += str(math.sin(t[i]) + (1.0/3.0) + math.sin(t[i] * 3))
                    y += str((1.0 / 2.0) * math.sin(t[i]) + (1.0/4.0) * math.sin(t[i] * 4))
                


        # last sample without "," after it.
        if (Channel == 1):
            self.rp.tx_txt('SOUR1:TRAC:DATA:DATA ' + x)

        if (Channel == 2):
            self.rp.tx_txt('SOUR2:TRAC:DATA:DATA ' + y)
        
        self.ConfigureSignalGen(Channel)

        return    
    
    
    
    
    def ConfigureSignalGen(self, Channel = 1):
        #sine
        if (self.GenSignalType[Channel -1] == 0):
            if (Channel == 1):
                self.rp.tx_txt('SOUR1:FUNC SINE')       
    
            if (Channel == 2):
                self.rp.tx_txt('SOUR2:FUNC SINE')        
            
        # square
        if (self.GenSignalType[Channel -1] == 1):
            if (Channel == 1):
                self.rp.tx_txt('SOUR1:FUNC SQUARE')       
    
            if (Channel == 2):
                self.rp.tx_txt('SOUR2:FUNC SQUARE')    
                
        # ARBITRARY
        if (self.GenSignalType[Channel -1] == 6):
            if (Channel == 1):
                self.rp.tx_txt('SOUR1:FUNC ARBITRARY')       
    
            if (Channel == 2):
                self.rp.tx_txt('SOUR2:FUNC ARBITRARY')    
                
        # Set configuration for all wave forms configuration
        if (Channel == 1):
            Ampl = ("%.3f" % self.Amplitude[0])
            self.rp.tx_txt('SOUR1:VOLT ' + str(Ampl))
            self.rp.tx_txt('SOUR1:FREQ:FIX ' + str(self.Frequency[0]))        

        if (Channel == 2):
            Ampl = ("%.3f" % self.Amplitude[1])
            self.rp.tx_txt('SOUR2:VOLT ' + str(Ampl))
            self.rp.tx_txt('SOUR2:FREQ:FIX ' + str(self.Frequency[1]))        
            
        return

    def EnableOutput(self, Channel = 1):
        if (Channel == 1):
            self.rp.tx_txt('OUTPUT1:STATE ON')
        if (Channel == 2):
            self.rp.tx_txt('OUTPUT2:STATE ON')
        return
        
    def EnableBothOutputs(self):
        self.rp.tx_txt('OUTPUT:STATE ON')
        return
    
    def PrintSettings(self):
        Duration = 1/ self.Frequency
        
        print("-------------------------------------------")
        print("Duration 1      : %.3f sec @ 16384 points" % (Duration[0]))
        print("Frequency 1     : %.0f Hz" % (self.Frequency[0] * 16384))
        print("Amplitude 1     : %.3f Volt" % self.Amplitude[0])
        print("-------------------------------------------")
        print("Duration 2      : %.3f sec @ 16384 points" % (Duration[1]))
        print("Frequency 2     : %.0f Hz" % (self.Frequency[1] * 16384))
        print("Amplitude 2     : %.3f Volt" % self.Amplitude[1])
        print("-------------------------------------------")
        return;    
        


