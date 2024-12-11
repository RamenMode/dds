from RingClient import RingClient
import signal
import os
from time import time, sleep
import uuid
import sys
import logging

logging.basicConfig(level=logging.INFO)

k = 1
current = 0
client_no = os.getenv("NODE_PORT")

def decrementk(signum, frame):
    global current
    global k
    current = 0
    return k - 0.2 if k != 0 else 0

try:
    client_no = os.getenv("NODE_PORT")
    signal.signal(signal.SIGALRM, decrementk)
    signal.setitimer(signal.ITIMER_REAL, 2, 2)

    chord_name = "ring32"

    logging.info(f"Client {client_no} starting at {time()}")

    r = RingClient(chord_name, os.getenv('NODE_IP'))
    while True:
        start = time()
        key = str(uuid.uuid4())[:8]
        r.update(key, str(uuid.uuid4())[:8])
        current += 1
        logging.info(f'{r.query(key)} from key {key}')
        current += 1
        r.delete(key)
        current += 1
        end = time()
        sleep((end-start)*k)
except Exception as e:
    logging.info(f"error {e}")
    logging.info("Exception")





