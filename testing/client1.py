from ..RingClient import RingClient
r = RingClient("ring23")
for _ in range(10):
    r.update("1", "Hello")
    print(r.query("1"))