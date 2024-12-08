from ..Node import Node
from ..RingClient import RingClient

node3 = Node('0.0.0.0', 9900, 900, "ring5")
node3.join("ring5")
node3.listen()