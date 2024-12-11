from ..Node import Node
from ..RingClient import RingClient

node4 = Node('0.0.0.0', 9380, 380, None, "ring20")
name_server = node4.read_nameserver()
for key in name_server[node4.chord_name]:
    print(f"Node {key} =====================")
    print(node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server[node4.chord_name][key]))