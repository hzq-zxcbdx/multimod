import sys
import subprocess

interface = "wlan0"

proc = subprocess.Popen(["iwconfig",interface],stdout=subprocess.PIPE, universal_newlines=True)
out, err = proc.communicate()


for line in out.split('\n'):
    if 'Quality' in line:
        print(line)


