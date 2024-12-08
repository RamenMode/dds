import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from RingClient import RingClient, name_server

del name_server["KLuke"][900]

r = RingClient("KLuke")

for _ in range(10):
    r.update("1", "Hello")
    print(r.query("1"))

name_server["KLuke"][900] = ("127.0.0.1", 9900)