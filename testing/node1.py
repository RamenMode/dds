from ..Node import Node
from ..RingClient import RingClient

# Let node 1 be the bootstrap node 

node1 = Node('0.0.0.0', 9020, 20, "ring8")
node1.create("ring8")
node1.listen()