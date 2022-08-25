#usr/bin/python3
# -*- coding: utf-8 -*-
from ast import LtE
import serial
import time

from time import sleep
ser = serial.Serial("/dev/ttyUSB2", 115200, timeout=0.5)

print(ser.isOpen())

while True:
    success_bytes = ser.write('at+csq\r'.encode())
    print(success_bytes)
    data = ser.read(100)
    data = str(data).split(':')
    data = data[1].split(',')
    data = data[0]
    signal_data = int(data)
    if(signal_data == 99):
            signal_is_ok = False
            signal_level = 0
    else:
        signal_level = signal_data*2 - 113
    
    print(signal_data)

    print(signal_level)

    sleep(2)

