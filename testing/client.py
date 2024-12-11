from RingClient import RingClient
import signal
import os
from time import time, sleep
import uuid
import sys
import logging


k = 1

current = 0

def decrementk(k):
    logging.info(f'{sys.argv[1]}, {current}')
    global current
    current = 0
    return k - 0.2 if k != 0 else 0

signal.signal(signal.SIGALRM, decrementk)
signal.setitimer(signal.ITIMER_REAL, 2, 2)

chord_name = "ring28"

r = RingClient(chord_name, os.getenv('NODE_IP'))

client_no = sys.argv[1]

logging.info(f"Client {sys.argv[1]} starting at {time()}")

while True:
    start = time()
    key = random_string = str(uuid.uuid4())[:8]
    r.update(key, random_string = str(uuid.uuid4())[:8])
    current += 1
    r.query(key)
    current += 1
    r.delete(key)
    current += 1
    end = time()
    sleep((end-start)*k)





