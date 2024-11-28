from ..Node import Node
from ..RingClient import RingClient, name_server

node4 = Node('127.0.0.1', 9380, 380)
print(node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][20]))
print(node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][110]))
print(node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][200]))
print(node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][290]))