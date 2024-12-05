from ..Node import Node
from ..RingClient import RingClient, name_server

node4 = Node('127.0.0.1', 9380, 380)
for key in name_server["KLuke"]:
    print(f"Node {key} =====================")
    print(node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][key]))