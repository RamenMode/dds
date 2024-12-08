from ..Node import Node
from ..RingClient import RingClient

node3 = Node('0.0.0.0', 9200, 200, "d4")
node3.join("d4")
node3.listen()
