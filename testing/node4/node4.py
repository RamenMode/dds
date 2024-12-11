from .Node import Node

node4 = Node('0.0.0.0', 9290, 290, None, "ring-4")
node4.join("ring-4")
node4.listen()