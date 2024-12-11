from ..RingClient import RingClient
r = RingClient("ring20")
for _ in range(10):
    r.update("1", "Hello")
    print(r.query("1"))