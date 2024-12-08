import socket
import json
import struct
import random
from Node import hash_it

name_server: dict[int, tuple[str, int]] = {
    "KLuke": {
        20: ("127.0.0.1", 9020),
        110: ("127.0.0.1", 9110),
        200: ("127.0.0.1", 9200),
        290: ("127.0.0.1", 9290),
        900: ("127.0.0.1", 9900)
    }
}

class RingClient:

    def __init__(self, name: str = "KLuke"):
        self.name = name
        self.host = '127.0.0.1'
    
    def _retrieve_nodes(self):
        # TODO Implement a Real Nameserver
        return name_server[self.name]
    
    def choose_node(self):
        # TODO contact the nameserver

        # just return server with node id 20 for now
        return 20

        #return random.choice(list(name_server[self.name].keys()))
    
    def obtain_successor(self, key):
        hash_val = hash_it(key) % 1024
        request = {"type": "function", "func_name": "find_successor", "args": {"hash": hash_val}}
        response = self.async_request(request, *name_server[self.name][self.choose_node()])
        return response["val"]["nodeid"]
    
    def update(self, key, value):
        server = self.obtain_successor(key)
        request = {"type": "value", "var_name": "storage", "val": (key, value), "get": False}
        response = self.send_request(request, *name_server[self.name][server])
        return response['success']

    def query(self, key):
        server = self.obtain_successor(key)
        request = {"type": "value", "var_name": "storage", "val": key, "get": True}
        response = self.send_request(request, *name_server[self.name][server])
        return response["val"]
        
    def delete(self, key):
        server = self.obtain_successor(key)
        request = {"type": "value", "var_name": "storage", "val": ("RESTRICTED_FOR_DELETE0x0x0", key), "get": False}
        response = self.send_request(request, *name_server[self.name][server])
        return response["val"]

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

    def async_request(self, request, host, port):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socke:
                    socke.bind((self.host, 0))
                    socke.listen()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((host, port))
                    # Make sure the requests location is specified
                    request["asynch"] = (self.host, socke.getsockname()[1]) # the port to async send back to
                    request_data = json.dumps(request).encode('utf-8')
                    request_length = len(request_data)
                    sock.sendall(struct.pack('!I', request_length))
                    sock.sendall(request_data)
                    # set a time out for receiving message
                    socke.settimeout(5)
                    
                    # Receive the response from the server
                    while True:
                        try:
                            connection, addr = socke.accept() # accept the eventual response
                            connection.settimeout(5)
                            length_header = b''
                            while len(length_header) < 4:
                                chunk = connection.recv(4 - len(length_header)) # recv from the new socket
                                length_header += chunk
                            m_length = struct.unpack('!I', length_header)[0]
                            response = connection.recv(m_length)
                            response = json.loads(response.decode('utf-8'))
                            return response
                        except Exception:
                            break
            except EOFError:
                #print(f"Client {peername} disconnected")
                sock.close()
            except Exception as e:
                print(str(e))
                print('Unhandled exception')