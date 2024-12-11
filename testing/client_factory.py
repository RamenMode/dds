import subprocess
import time

counter = 0
while True:
    counter += 1
    subprocess.run(['python3', 'client.py', counter])
    time.sleep(10)