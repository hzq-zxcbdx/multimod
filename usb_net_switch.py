#usr/bin/python3
# -*- coding: utf-8 -*-
from ast import LtE
import serial
import time

from time import sleep
ser = serial.Serial("/dev/ttyUSB2", 115200, timeout=0.5)

print(ser.isOpen())

while True:
    success_bytes = ser.write('AT+QNWPREFCFG="mode_pref",LTE\r'.encode())

    ser.write('at+cfun=1,1\r'.encode())

    sleep(2)

