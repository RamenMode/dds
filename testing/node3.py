from ..Node import Node
from ..RingClient import RingClient

node3 = Node('0.0.0.0', 9200, 200, None, "ring32")
node3.join("ring32")
node3.listen()
