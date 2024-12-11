import subprocess
import time

counter = 0
while True:
    counter += 1
    process = subprocess.Popen(['python3', 'client.py', str(counter)])
    time.sleep(10)