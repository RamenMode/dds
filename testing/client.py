from RingClient import RingClient
import signal
import os
from time import time, sleep
import uuid
import sys
import logging


k = 1
current = 0
client_no = os.getenv("NODE_PORT")

def decrementk(signum, frame):
    global current
    global k
    logging.info(f"{os.getenv(client_no)}, {current}")
    current = 0
    return k - 0.2 if k != 0 else 0

signal.signal(signal.SIGALRM, decrementk)
signal.setitimer(signal.ITIMER_REAL, 2, 2)

chord_name = "ring20"

r = RingClient(chord_name, os.getenv('NODE_IP'))

logging.info(f"Client {client_no} starting at {time()}")

while True:
    start = time()
    key = str(uuid.uuid4())[:8]
    r.update(key, str(uuid.uuid4())[:8])
    current += 1
    r.query(key)
    current += 1
    r.delete(key)
    current += 1
    end = time()
    sleep((end-start)*k)





