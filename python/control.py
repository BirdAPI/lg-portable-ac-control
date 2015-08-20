#!/usr/bin/env python

import time
import serial

def ctof(c):
    return int(c * 9.0 / 5.0 + 32)
    
def binary(val, digits=4):
    return ('{0:0'+str(digits)+'b}').format(int(val))

class Mode(object):
    COOL = 1
    DRY = 2
    FAN = 3
    ENERGY_SAVER = 4    
   
class Fan(object):
    LOW = 1
    MED = 2
    HIGH = 3 
 
class Controller(object):
    def __init__(self):
        self.serial = serial.Serial('/dev/ttyACM0', 9600)
        print self.serial.readline().strip()
        
    def send_binary(self, binary):
        self.serial.write("^{0}$".format(binary))
        print self.serial.readline().strip()
    
    def send_command(self, command):
        self.send_binary(command.get_payload())
        
 
class Command(object):
    def __init__(self, **kwargs):
        self.payload = [0] * 9
        self.celsius = False
        self.power_on = False
        self.power_off = False
        self.timer = False
        self.timer_hours = 0
        self.fan = Fan.LOW
        self.temp = 60
        self.auto_clean = False
        self.auto_swing = False
        self.mode = Mode.COOL
        
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        
    def _set_temp_bytes(self):
        if self.celsius:
            self.payload[7] |= 0b1000 << 4
            f = ctof(self.temp)
            self.temp_offset = f - 59
        else:
            self.temp_offset = self.temp - 59
        self.payload[1] |= int((self.temp_offset - 1 + int(self.temp_offset / 9)) / 2) << 4
        self.payload[3] = self.temp_offset
        
    def _set_timer_bytes(self):
        if self.timer:
            self.payload[1] |= 0b1000
            self.payload[7] |= 0b0010
            self.payload[2] = self.timer_hours
            
    def _set_power_bytes(self):
        if not self.power_off:
            self.payload[1] |= 0b0010
        if self.power_on or self.power_off:
            self.payload[7] |= 0b1000
    
    def _set_misc_bytes(self):
        self.payload[6] |= self.fan << 4
        self.payload[6] |= self.mode
        if self.auto_clean:
            self.payload[7] |= 0b0100
        if self.auto_swing:
            self.payload[1] |= 0b0001
        
    def compute_checksum(self):
        self.checksum = 0
        for i in range(9):
            self.checksum += self.payload[i]
        while self.checksum > 255:
            self.checksum -= 256
        self.payload[8] = self.checksum
        
    def get_payload(self):
        self.payload = [0] * 9
        self.payload[0] = 0x55
        self._set_temp_bytes()
        self._set_timer_bytes()
        self._set_power_bytes()
        self._set_misc_bytes()
        self.compute_checksum()
        return ''.join([binary(token, 8) for token in self.payload])
 
def main():
    control = Controller()
    c85 = Command(celsius=False, timer=False,
            temp=85, fan=Fan.LOW, auto_swing=False, auto_clean=True, 
            mode=Mode.COOL, power_on=False, 
            power_off=False)
    control.send_command(c85)
    time.sleep(10)
    c82 = Command(celsius=False, timer=False,
        temp=82, fan=Fan.LOW, auto_swing=False, auto_clean=True, 
        mode=Mode.COOL, power_on=False, 
        power_off=False)
    control.send_command(c82)
 
if __name__ == "__main__":
    main()
 