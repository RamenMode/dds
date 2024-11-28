from ..Node import Node
from ..RingClient import RingClient, name_server

# Let node 1 be the bootstrap node 

node1 = Node('127.0.0.1', 9020, 20)
node1.create()
node1.listen()