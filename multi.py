#!/usr/bin/python
# encoding: utf-8
# -*- coding: utf8 -*-

import os
import sys
import netifaces
import logging
import serial
import time
import subprocess
from time import sleep
from datetime import datetime
from datetime import timedelta

curr_time=datetime.now() 
today=(curr_time.strftime("%Y-%m-%d"))
print(today)



state_starting = 0
state_transmit_usb = 1
state_transmit_wifi = 2
state_transmit_mul = 3
state_usb_net_switch = 4
state_net_error = 5

error_usb_net = 0
error_com = 0
error_wifi = 0

def log_init(filename):
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.DEBUG)
    test_log = logging.FileHandler(filename,'a',encoding='utf-8')
    test_log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(filename)s - line:%(lineno)d - %(levelname)s - %(message)s -%(process)s')
    test_log.setFormatter(formatter)
    logger.addHandler(test_log)
    return logger


def ser_open(com,log):
    try:
        ser = serial.Serial(com, 115200, timeout=0.5)
        if(ser.isOpen()):
            log.info(com + '已打开')
            is_open = True
        else:
            log.error(com + '未成功打开')
            is_open = False

        return ser,is_open
    except Exception:
        log.error(com + '错误，请检查输入的串口名称')
        is_open = False
        return 0,is_open

    

def get_wlan_strength(interface,log):
    proc = subprocess.Popen(["iwconfig",interface],stdout=subprocess.PIPE, universal_newlines=True)
    out, err = proc.communicate()

    for line in out.split('\n'):
        if 'Quality' in line:
            log.info(line)
            link_quality = round(float(line[23:25])/float(line[26:29]),3)
            signal_level = int(line[43:46])
            log.info('连接质量：' + str(link_quality) + '    信号强度：' + str(signal_level))
            
            return link_quality,signal_level
    
    log.error('检测wlan状态失败')
    return 0,0


def get_usb_strength(com,log):
    global error_usb_signal
    try:
        success_bytes = com.write('at+csq\r'.encode())
        # print(success_bytes)
        data = com.read(100)
        log.info(data)
        data = str(data).split(':')
        data = data[1].split(',')
        data = data[0]
        signal_data = int(data)
        if(signal_data == 99):
            signal_is_ok = False
            signal_level = 0
            error_usb_signal += 1
        else:
            signal_is_ok = True
            signal_level = signal_data*2 - 113
        return signal_level,signal_is_ok
    except Exception:
        log.error('获取信号错误，尝试重新获取')
        return 0,0


def get_ip(interface,log):
    try:
        ip =  netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        log.info(interface+'的ip地址为'+ip)
        return ip
    except Exception:
        log.error('没有'+ interface)
        return 0
    
def get_net_type(com,log):
    try:
        success_bytes = com.write('at+qnwinfo\r'.encode())
        data = com.read(100)
        data = str(data).split('"')
        is_4g = 'FDD LTE' in data
        is_5g = 'NR5G-SA' in data
        if (is_4g or is_5g):
            net_type = data[1]
            net_band = data[3]
            log.info(data)
        else:
            log.error('当前未成功获取网络状态')
            net_type = 0
            net_band = 0
        return net_type,net_band
    except Exception:
        log.error('获取网络信息错误，检查串口是否冲突？')
        return 0,0

def usb_net_switch(com,log):
    try:
        usb_type,usb_band = get_net_type(com,log)
        if(usb_type == 'FDD LTE'):
            success_bytes = com.write('AT+QNWPREFCFG="mode_pref",NR5G\r'.encode())
        elif(usb_type == 'NR5G-SA'):
            success_bytes = com.write('AT+QNWPREFCFG="mode_pref",LTE\r'.encode())

        com.write('at+cfun=1,1\r'.encode())
        log.info('网络已切换，正在重启')
    except Exception:
        log.error('获取网络信息错误，检查串口是否冲突？')
        return 0,0


def transmit_vedio(video_path,interface,destination,destination_ip,destination_path,usb_type,log):
    net_switch(interface)
    sleep(0.5)
    if(interface == 'wlan0'):
        print('now use:' + interface)
    else:
        print('now use:' + usb_type)
    ip = get_ip(interface,log)
    cmd = 'scp -o BindAddress='+ ip +' -o ConnectTimeout=3 -i /home/pi/xd '+ video_path +' '+ destination +'@'+ destination_ip +':'+ destination_path
    ret = subprocess.run(cmd,shell=True)
    if(ret.returncode == 1):
        log.error('视频传输失败')
        return 0
    if(ret.returncode == 0):
        log.info(video_path + '传输成功')
        return 1

def net_switch(interaface):
    os.system('sudo ifmetric ' + interaface)



    
    

def error_handle(error,log):
    a = 1

# def 


if __name__ == "__main__":
    state = state_starting
    test = 0
    # 设置目的地信息
    video_path = '/home/pi/test1.mp4'
    destination = 'ubuntu'
    destination_ip = '124.221.243.112'
    destination_path = '/home/ubuntu'
    interface_to_use = 'wlan0'
    mul_log = log_init(filename=today + '.log')
    usb_ip =  get_ip('usb0',mul_log)
    wlan_ip =  get_ip('wlan0',mul_log)
    if(wlan_ip == 0 and usb_ip == 0):
        state = state_net_error
    elif(wlan_ip == 0 ):
        state = state_transmit_usb
    elif(usb_ip == 0 ):
        state = state_transmit_wifi
    else:
        state = state_transmit_mul
    mul_log.info('模块目前状态为：' + str(state))
    wlan_quality,wlan_signal = get_wlan_strength('wlan0',mul_log)
    mul_ser,ser_isopen  = ser_open('/dev/ttyUSB2',mul_log)
    if(ser_isopen == False):
        error_com = 1
    mul_log.info('启动完成')
    
    while(1):
        
        test += 1
        print(test)
        sleep(2)
        wlan_quality,wlan_signal = get_wlan_strength('wlan0',mul_log)
        usb_type,usb_band = get_net_type(mul_ser,mul_log)
        usb_signal,usb_signal_is_ok = get_usb_strength(mul_ser,mul_log)
        print('wifi质量；',wlan_quality,' wifi信号强度为：',wlan_signal,'dbm')
        print('移动网络信号强度为:',usb_signal,'dbm')
        if(wlan_quality < 0.95):
            interface_to_use = 'usb0'
        else:
            interface_to_use = 'wlan0'
        
        transmit_ok = transmit_vedio(video_path,interface_to_use,destination,destination_ip,destination_path,usb_type,mul_log)
        if(transmit_ok == 1):
            print('传输成功')
        else:
            print('传输失败')

        if(test == 3):
            usb_net_switch(mul_ser,mul_log)


    # while(1):
    #     print('test')
    #     sleep(1)















