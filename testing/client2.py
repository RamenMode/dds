from ..RingClient import RingClient

r = RingClient()
nodes = r._retrieve_nodes()
for i in range(50):
    print(r.test_comm_rpc(nodes[110], nodes[20]))