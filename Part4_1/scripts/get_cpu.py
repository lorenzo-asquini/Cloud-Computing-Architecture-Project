import psutil
import os
import time

pid = int(os.popen("cat /var/run/memcached/memcached.pid").read().strip())
process = psutil.Process(pid)

while(True):
    # Print the time in milliseconds and the cpu usage of memcached
    print(f"{int(time.time() * 1000)} {process.cpu_percent(interval=0.5)}")