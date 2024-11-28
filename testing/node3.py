from ..Node import Node
from ..RingClient import RingClient, name_server

node3 = Node('127.0.0.1', 9200, 200)
node3.join()
node3.listen()
