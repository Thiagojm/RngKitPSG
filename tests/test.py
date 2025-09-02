import rng_module as rm
import time
addr, port, max_msg_size = '127.0.0.1', 1200, 32768
command = f"src\\bin\\seedd.exe --no-qa -f0 --udp-out 127.0.0.1:1200"

rm.kill_seedd()
time.sleep(1)
seedd_process = rm.start_seedd(command)
time.sleep(2)
chunk = rm.read_from_deamon(addr, port, 8, max_msg_size)
print(chunk)