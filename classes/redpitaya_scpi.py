"""SCPI access to Red Pitaya."""

import socket
import struct
import codecs
import numpy as np

__author__ = "Luka Golinar, Iztok Jeras"
__copyright__ = "Copyright 2015, Red Pitaya"

class scpi (object):
    """SCPI class used to access Red Pitaya over an IP network."""
    delimiter = '\r\n'

    def __init__(self, host, timeout=None, port=5000):
        """Initialize object and open IP connection.
        Host IP should be a string in parentheses, like '192.168.1.100'.
        """
        self.host    = host
        self.port    = port
        self.timeout = timeout

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._socket.connect((host, port))

        except socket.error as e:
            print('SCPI >> connect({:s}:{:d}) failed: {:s}'.format(host, port, e))

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def close(self):
        """Close IP connection."""
        self.__del__()

    def rx_txt(self, chunksize = 4096):
        """Receive text string and return it after removing the delimiter."""
        msg = ''
        while 1:
            chunk = self._socket.recv(chunksize + len(self.delimiter)).decode('utf-8') # Receive chunk size of 2^n preferably
            msg += chunk
            if (len(chunk) and chunk[-2:] == self.delimiter):
                break
        return msg[:-2]

    # def rx_arb(self):
    #     numOfBytes = 0
    #     """ Recieve binary data from scpi server"""
    #     str=''
    #     while (len(str) != 1):
    #         str = (self._socket.recv(1))
    #     if not (str.decode('utf-8') == '#'):
    #         print(str)
    #         return False
        
    #     str=''
        
    #     while (len(str) != 1):
    #         str = (self._socket.recv(1))

    #     print(str)
    #     numOfNumBytes = int(str)
    #     print(numOfNumBytes)
        
    #     if not (numOfNumBytes > 0):
    #         print(str)
    #         return False
        
    #     str=''
        
    #     while (len(str) != numOfNumBytes):
    #         tmp = (self._socket.recv(1))
    #         str += tmp.decode('utf-8')
    #     numOfBytes = int(str)
        
    #     str=''
        
    #     while (len(str) != numOfBytes):
    #         str += (self._socket.recv(1))
    #         print(str)
    #     return str
    
    
    def rx_bin(self):
        # The first thing it sends is always a #
        #
        buf = self._socket.recv(1)
        print(buf.decode('utf-8'))

        # The second thing it sends is the number of digits in the byte count. 
        buf = self._socket.recv(1)
        digits_in_byte_count = int(buf)
        print(digits_in_byte_count)

        # The third thing it sends is the byte count
        # buf = self._socket.recv(digits_in_byte_count)
        buf = self._socket.recv(5)
        print(buf.decode('utf-8'))
        byte_count = int(buf)

        # buf = []
        # while len(buf) != byte_count:
        #     buf.append(self._socket.recv(1))

        # buffer_size = int(byte_count / 4)
        # 16384
        # 16384
        result = np.empty(16384, dtype = np.int16)
        size = self._socket.recv_into(result)

        return result


    def rx_bin_status(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        buf = self._socket.recv(100)
        tmp = buf.decode('utf-8')

        return tmp
        

    def tx_txt(self, msg):
        """Send text string ending and append delimiter."""
        return self._socket.send((msg + self.delimiter).encode('utf-8'))

    def txrx_txt(self, msg):
        """Send/receive text string."""
        self.tx_txt(msg)
        return self.rx_txt()

# IEEE Mandated Commands

    def cls(self):
        """Clear Status Command"""
        return self.tx_txt('*CLS')

    def ese(self, value: int):
        """Standard Event Status Enable Command"""
        return self.tx_txt('*ESE {}'.format(value))

    def ese_q(self):
        """Standard Event Status Enable Query"""
        return self.txrx_txt('*ESE?')

    def esr_q(self):
        """Standard Event Status Register Query"""
        return self.txrx_txt('*ESR?')

    def idn_q(self):
        """Identification Query"""
        return self.txrx_txt('*IDN?')

    def opc(self):
        """Operation Complete Command"""
        return self.tx_txt('*OPC')

    def opc_q(self):
        """Operation Complete Query"""
        return self.txrx_txt('*OPC?')

    def rst(self):
        """Reset Command"""
        return self.tx_txt('*RST')

    def sre(self):
        """Service Request Enable Command"""
        return self.tx_txt('*SRE')

    def sre_q(self):
        """Service Request Enable Query"""
        return self.txrx_txt('*SRE?')

    def stb_q(self):
        """Read Status Byte Query"""
        return self.txrx_txt('*STB?')

# :SYSTem

    def err_c(self):
        """Error count."""
        return rp.txrx_txt('SYST:ERR:COUN?')

    def err_c(self):
        """Error next."""
        return rp.txrx_txt('SYST:ERR:NEXT?')# -*- coding: utf-8 -*-

