from ..Node import Node
from ..RingClient import RingClient

node4 = Node('0.0.0.0', 9290, 290, "d4")
node4.join("d4")
node4.listen()