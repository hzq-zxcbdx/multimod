import os
import subprocess

# //video_path,interface,destination_1,destination_ip_1,destination_path
def transmit_vedio():
    ip = '192.168.42.3'
    path = '/home/pi/test1.mp4'
    destination = 'ubuntu'
    destination_ip = '124.221.243.112'
    destination_path = '/home/ubuntu'

    cmd = 'scp -o BindAddress='+ ip +' -o ConnectTimeout=2 -i /home/pi/xd '+ path +' '+ destination +'@'+ destination_ip +':'+ destination_path

    # ret = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE, universal_newlines=True)
    ret = subprocess.run(cmd,shell=True)

    # out, err = ret.communicate()

    # print('out:',out)
    print(ret.returncode)

    # os.system(cmd)

transmit_vedio()


