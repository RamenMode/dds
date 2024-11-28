from ..Node import Node
from ..RingClient import RingClient, name_server

node4 = Node('127.0.0.1', 9290, 290)
node4.join()
node4.listen()
node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][20])
node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][110])
node4.send_request({"type": "value", "var_name": "all", "get": False}, *name_server["KLuke"][200])
request = {"type": "function", "func_name": "find_predecessor", "args": {"hash": 290}}
response = node4.async_request(request, "127.0.0.1", 9020) # this find's the successor which is this node's successor)
print('hello')
print('hey', response)
# 110 200
# 200 20
# 20 110