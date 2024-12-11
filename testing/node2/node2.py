from .Node import Node

node2 = Node('0.0.0.0', 9110, 110, None, "ring-4")
node2.join("ring-4")
node2.listen()
#node2.send_request({"type": "value"}, *name_server["KLuke"][20])

