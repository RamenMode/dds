from ..Node import Node
from ..RingClient import RingClient

node4 = Node('0.0.0.0', 9290, 290, None, "ring22")
node4.join("ring22")
node4.listen()