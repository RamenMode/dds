from ..Node import Node
from ..RingClient import RingClient

node4 = Node('0.0.0.0', 9290, 290, "ring7")
node4.join("ring7")
node4.listen()