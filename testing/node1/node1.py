from .Node import Node

# Let node 1 be the bootstrap node 

node1 = Node('0.0.0.0', 9020, 20, None, "ring-4")
node1.create("ring-4")
node1.listen()