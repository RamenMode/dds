from ..Node import Node
from ..RingClient import RingClient

node3 = Node('0.0.0.0', 9200, 200, None, "ring23")
node3.join("ring23")
node3.listen()
