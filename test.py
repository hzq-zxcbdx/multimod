#!/usr/bin/python3
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

state_starting = 0
state_transmit_4G = 1
state_transmit_5G = 2
state_transmit_wifi = 2
state_transmit_mul = 3
state_usb_net_switch = 4
state_net_error = 5

error_usb_net = 0
error_com = 0
error_wifi = 0

curr_time = datetime.now()
today = (curr_time.strftime("%Y-%m-%d"))
print(today)

state = state_starting


def log_init(filename):
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.DEBUG)
    test_log = logging.FileHandler(filename, 'a', encoding='utf-8')
    test_log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s - line:%(lineno)d - %(levelname)s - %(message)s -%(process)s')
    test_log.setFormatter(formatter)
    logger.addHandler(test_log)
    return logger


def ser_open(com, log):
    try:
        ser = serial.Serial(com, 115200, timeout=0.5)
        if (ser.isOpen()):
            log.info(com + '已打开')
            is_open = True
        else:
            log.error(com + '未成功打开')
            is_open = False

        return ser, is_open
    except Exception:
        log.error(com + '错误，请检查输入的串口名称')
        is_open = False
        return 0, is_open


def get_wlan_strength(interface, log):
    proc = subprocess.Popen(["iwconfig", interface], stdout=subprocess.PIPE, universal_newlines=True)
    out, err = proc.communicate()

    for line in out.split('\n'):
        if 'Quality' in line:
            log.info(line)
            link_quality = round(float(line[23:25]) / float(line[26:29]), 3)
            signal_level = int(line[43:46])
            log.info('连接质量：' + str(link_quality) + '    信号强度：' + str(signal_level))

            return link_quality, signal_level

    log.error('检测wlan状态失败')
    return 0, 0


def get_net_strength(com, log):
    global error_usb_net
    try:
        success_bytes = com.write('at+csq\r'.encode())
        # print(success_bytes)
        data = com.read(100)
        log.info(data)
        data = str(data).split(':')
        data = data[1].split(',')
        data = data[0]
        signal_data = int(data)
        if (signal_data == 99):
            error_usb_net += 1
            signal_is_ok = False
            signal_level = 0
        else:
            signal_is_ok = True
            signal_level = signal_data * 2 - 113
        return signal_level, signal_is_ok
    except Exception:
        log.error('获取信号错误，尝试重新获取')
        return 0, 0


def get_ip(interface, log):
    try:
        ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        log.info(interface + '的ip地址为' + ip)
        ip_is_right = '192.168' in ip
        if (ip_is_right):
            return ip
        else:
            return 0
    except Exception:
        log.error('没有' + interface)
        return 0


def get_net_type(com, log):
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
        return net_type, net_band
    except Exception:
        log.error('获取网络信息错误，检查串口是否冲突？')
        return 0, 0


def usb_net_switch(com, log):
    try:
        usb_type, usb_band = get_net_type(com, log)
        if (usb_type == 'FDD LTE'):
            success_bytes = com.write('AT+QNWPREFCFG="mode_pref",NR5G\r'.encode())
        elif (usb_type == 'NR5G-SA'):
            success_bytes = com.write('AT+QNWPREFCFG="mode_pref",LTE\r'.encode())

        com.write('at+cfun=1,1\r'.encode())
        log.info('网络已切换，正在重启')
        print('串口是否关闭：' + com.isOpen())
        com.close()
        sleep(2)
    except Exception:
        log.error('获取网络信息错误，检查串口是否冲突？')
        return 0, 0


def transmit_vedio(video_path, interface, destination, destination_ip, destination_path, log):
    net_switch(interface)
    sleep(0.5)  # 网络切换需要一定时间
    if (interface == 'wlan0'):
        print('now use:' + interface)
    elif (interface == 'usb0'):
        print('now use: 4G')
    elif (interface == 'usb1'):
        print('now use: 5G')
    ip = get_ip(interface, log)
    cmd = 'scp -o BindAddress=' + ip + ' -o ConnectTimeout=3 -i /home/pi/xd ' + video_path + ' ' + destination + '@' + destination_ip + ':' + destination_path
    ret = subprocess.run(cmd, shell=True)
    if (ret.returncode == 1):
        log.error('视频传输失败')
        return 0
    if (ret.returncode == 0):
        log.info(video_path + '传输成功')
        return 1


def net_switch(interaface):
    os.system('sudo ifmetric ' + interaface)


def state_switch(log):
    global state
    ip_4G = get_ip('usb0', log)
    ip_5G = get_ip('usb1', log)
    wlan_ip = get_ip('wlan0', log)

    if (wlan_ip == 0 and ip_4G == 0 and ip_5G == 0):
        state = state_net_error
    elif (wlan_ip):
        state = state_transmit_usb
    elif (ip_4G == 0):
        state = state_transmit_wifi
    else:
        state = state_transmit_mul


# 错误处理函数，获取错误情况进行处理

def error_handle(log):
    global error_usb_net
    global error_com
    global error_wifi
    print('error_com:', error_com)
    print('error_usb_net:', error_usb_net)
    print('error_wifi:', error_wifi)

    restart_time_left = 45
    if (error_usb_net > 3):
        log.error('移动网络无信号，正在切换')
        usb_net_switch(mul_ser, mul_log)
        while (restart_time_left):
            sleep(1)
            restart_time_left -= 1
            print('重启进度：', int((45 - restart_time_left) / 45 * 100))
        error_usb_net = 0


# def


if __name__ == "__main__":
    test = 0
    # 设置接收端信息
    video_path = '/home/pi/test3.mp4'
    destination = 'ubuntu'
    destination_ip = '124.221.243.112'
    destination_path = '/home/ubuntu/live/mediaServer'
    interface_to_use = 'wlan0'
    mul_log = log_init(filename=today + '.log')
    # state_switch(mul_log)
    mul_log.info('模块目前状态为：' + str(state))
    wlan_quality, wlan_signal = get_wlan_strength('wlan0', mul_log)
    ser_4G, ser_4G_isopen = ser_open('/dev/ttyS0', mul_log)
    ser_5G, ser_5G_isopen = ser_open('/dev/ttyUSB2', mul_log)

    while (1):
        # state_switch()
        net_type_4G = get_net_type(ser_4G, mul_log)
        net_type_5G = get_net_type(ser_5G, mul_log)
        signal_4G = get_net_strength(ser_4G, mul_log)
        signal_5G = get_net_strength(ser_5G, mul_log)
        print('4g', signal_4G, '5g', signal_5G)
        interface_to_use = 'wlan0'
        transmit_ok = transmit_vedio(video_path, interface_to_use, destination, destination_ip, destination_path,
                                     mul_log)

        sleep(2)













