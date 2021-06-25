import sys
import time
import redpitaya_scpi as scpi
import numpy as np

# https://github.com/RedPitaya/RedPitaya/blob/master/scpi-server/src/scpi-commands.c#L96-L204
# <source> = {DISABLED, NOW, CH1_PE, CH1_NE, CH2_PE, CH2_NE, EXT_PE, EXT_NE, AWG_PE, AWG_NE} Default: DISABLED
# <status> = {WAIT, TD}
# <time> = {value in ns}
# <counetr> = {value in samples}
# <gain> = {LV, HV}
# <level> = {value in V}
# <mode> = {AC,DC}

class redpitaya_scope:
    rp = []
    NrSamples           = int(16384)
    Decimation          = 1;
    Frequency           = 125e6/(Decimation * NrSamples)
    SampleFrequency     = 125e6
    Duration            = (Decimation * NrSamples) / SampleFrequency
    Gain                = np.array([1, 1])
    Probe               = np.array([1, 1])
    TriggerDelay        = 0
    Decimation_Array    = np.array([1, 8, 64, 1024, 8192, 65536])
    Average             = 0;
    
    def __init__(self, pitaya):
        # self.ip = ip
        # self.rp = scpi.scpi(ip)
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
    # Not all decimations do work. 
    # This is error in the documentation on the website.
    # I have tested and only: {1,8,64,1024,8192,65536} do works.
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
    
    def WriteDecimation(self):
        self.rp.tx_txt('ACQ:DEC ' + str(self.Decimation) )
        return
    
    #==============================================================================
    # Options are: 
    # {DISABLED, NOW, CH1_PE, CH1_NE, CH2_PE, CH2_NE, EXT_PE, EXT_NE, AWG_PE, AWG_NE}
    # Delay will shift the plot. 
    # 8192 will restult in triggered value as first sample of the data.
    # 0 will result in triggered value as mid point of the data
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
        print("Trigger Level   : %.3f Volt" % (self.TriggerLevel))
        print("Range 1         : +/-%.1f Volt" % self.Gain[0])
        print("Range 1         : +/-%.1f Volt" % self.Gain[1])
        print("Probe 1         : %.0fx" % self.Probe[0])
        print("Probe 2         : %.0fx" % self.Probe[1])
        return;

    def GetTimeVector(self):
        TimeVector = np.arange(self.NrSamples) / self.Frequency
        return TimeVector
    
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

    # def init_scope():
    # # https://github.com/RedPitaya/RedPitaya/blob/master/scpi-server/src/scpi-commands.c#L96-L204
    # rp_s.tx_txt('ACQ:RST')
    # rp_s.tx_txt('ACQ:START')

    # # rp_s.tx_txt('ACQ:SOUR1:GAIN HV')
    # rp_s.tx_txt('ACQ:SOUR1:GAIN LV')
    # rp_s.tx_txt('ACQ:TRIG:LEV 0')
    # rp_s.tx_txt('ACQ:TRIG:DLY 8192')
    # # rp_s.tx_txt('ACQ:SOUR2:GAIN HV')
    # rp_s.tx_txt('ACQ:SOUR2:GAIN LV')

    # # rp_s.tx_txt('ACQ:DEC 4096')
    # # rp_s.tx_txt('ACQ:DEC 256')
    # rp_s.tx_txt('ACQ:DEC 16')

    
    