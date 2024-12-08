from ..Node import Node
from ..RingClient import RingClient

node3 = Node('0.0.0.0', 9200, 200, "ring2")
node3.join("ring2")
node3.listen()
