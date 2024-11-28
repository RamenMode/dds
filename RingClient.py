import socket
import json
import struct

name_server: dict[int, tuple[str, int]] = {
    "KLuke": {
        20: ("127.0.0.1", 9020),
        110: ("127.0.0.1", 9110),
        200: ("127.0.0.1", 9200),
        290: ("127.0.0.1", 9290)
    }
}

class RingClient:

    def __init__(self, name: str = "KLuke"):
        self.name = name
    
    def _retrieve_nodes(self):
        # TODO Implement a Real Nameserver
        return name_server[self.name]

    def update(self, key: int, value: object, host_port):
        pass

    def query(self, key: int, host_port):
        pass

    def delete(self, key: int, host_port):
        pass

    def test_comm_rpc(self, caller, callee):

        request = {"type": "function", "func_name": "test_rpc", "args": {"host": callee[0], "port": callee[1]}, "response": False}
        response = self.send_request(request, *caller)
        return response

    def send_request(self, request, host, port):
        while True:
            print(f'sending request to {host} {port}')
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, port))
                # Send a request to the server
                request_data = json.dumps(request).encode('utf-8')
                request_length = len(request_data)
                sock.sendall(struct.pack('!I', request_length))
                sock.sendall(request_data)

                print(f"[send_request] sending the request to {host} {port}, waiting for response")
                # set a time out for receiving message
                sock.settimeout(5)
                
                # Receive the response from the server
                length_header = b''
                while len(length_header) < 4:
                    chunk = sock.recv(4 - len(length_header))
                    length_header += chunk
                m_length = struct.unpack('!I', length_header)[0]
                response = sock.recv(m_length)
                response = json.loads(response.decode('utf-8'))
                print("[send_request] the response is ", response)
                return response
            except EOFError:
                #print(f"Client {peername} disconnected")
                sock.close()
                print('i mean')
            except Exception as e:
                print(str(e))
                print('Unhandled exception')