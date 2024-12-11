from ..Node import Node
from ..RingClient import RingClient

node2 = Node('0.0.0.0', 9110, 110, None, "ring32")
node2.join("ring32")
node2.listen()
#node2.send_request({"type": "value"}, *name_server["KLuke"][20])

