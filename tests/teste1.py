import subprocess
import time

import serial
from serial.tools import list_ports

values = {"bit_ac": False, 'true3_ac': False, "true3_bit_ac": True}

def check_usb(values):
    if values["bit_ac"]:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(f"src/bin/seedd.exe --limit-max-xfer --no-qa -f0 -b 1",
            stdout=subprocess.PIPE, startupinfo=startupinfo)
        chunk = proc.stdout.read()
        if chunk:
            print(chunk)
        else:
            print("faio")
    elif values['true3_ac']:
        ports_avaiable = list(list_ports.comports())
        rng_com_port = None
        for temp in ports_avaiable:
            if temp[1].startswith("TrueRNG"):
                if rng_com_port == None:  # always chooses the 1st TrueRNG found
                    rng_com_port = str(temp[0])
        if rng_com_port:
            print(rng_com_port)
        else:
            print("faio")
    elif values["true3_bit_ac"]:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.Popen(f"src/bin/seedd.exe --limit-max-xfer --no-qa -f0 -b 1", stdout=subprocess.PIPE,
                                startupinfo=startupinfo)
        chunk = proc.stdout.read()
        ports_avaiable = list(list_ports.comports())
        rng_com_port = None
        for temp in ports_avaiable:
            if temp[1].startswith("TrueRNG"):
                if rng_com_port == None:  # always chooses the 1st TrueRNG found
                    rng_com_port = str(temp[0])
        if rng_com_port and chunk:
            print(chunk, rng_com_port)
        else:
            print("faio")

t0 = time.time()
check_usb(values)
t1 = time.time()
print(t1 - t0)