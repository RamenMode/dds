from ..RingClient import RingClient
r = RingClient("ring-3")
for _ in range(10):
    r.update("1", "Hello")
    print(r.query("1"))