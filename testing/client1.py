from ..RingClient import RingClient
r = RingClient("d4")
for _ in range(10):
    r.update("1", "Hello")
    print(r.query("1"))