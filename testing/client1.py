from ..RingClient import RingClient
r = RingClient("ring8")
for _ in range(10):
    r.update("1", "Hello")
    print(r.query("1"))

    # global k
    # update_K
    # k = k - 0.2
    # k = 0

    # initial time
    # request
    # response
    # final time
    # time.sleep(final time - initial time)
    # 50%

    # initial time
    # request
    # response
    # final time
    # time.sleep((final time - initial time)*0.7)
    # 65%

    # 100%