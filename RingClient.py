import socket
import json
import struct
import random
from .Node import hash_it
from collections import defaultdict
import time
import http.client
import logging
from time import sleep

logging.basicConfig(level=logging.INFO)

class RingClient:

    def __init__(self, name: str = "KLuke", host='0.0.0.0'):
        self.name = name
        self.host = host
        self.chord_name = name
        self.name_server = self._retrieve_nodes()
        #logging.info(f"name server is {self.name_server}")

    def _retrieve_nodes(self):
        return self.read_nameserver()

    def choose_node(self):
        # TODO contact the nameserver
        return random.choice(list(self.name_server[self.name].keys()))

    def obtain_successor(self, key):
        hash_val = hash_it(key) % 1024
        request = {"type": "function", "func_name": "find_successor", "args": {"hash": hash_val}}
        response = self.async_request(request, *self.name_server[self.name][self.choose_node()])
        return response["val"]["nodeid"]
    def get_all(self, nodeId):
        request = {"type": "value", "var_name": "all", "get": True}
        response = self.send_request(request, *self.name_server[self.name][nodeId])
        #print(response)
        return response["val"]

    def update(self, key, value):
        server = self.obtain_successor(key)
        request = {"type": "value", "var_name": "storage", "val": (key, value), "get": False}
        response = self.send_request(request, *self.name_server[self.name][server])
        return response['success']

    def query(self, key):
        server = self.obtain_successor(key)
        request = {"type": "value", "var_name": "storage", "val": key, "get": True}
        response = self.send_request(request, *self.name_server[self.name][server])
        #print(response)
        return response["val"]

    def delete(self, key):
        server = self.obtain_successor(key)
        request = {"type": "value", "var_name": "storage", "val": ("RESTRICTED_FOR_DELETE0x0x0", key), "get": False}
        response = self.send_request(request, *self.name_server[self.name][server])
        return response["success"]

    def test_comm_rpc(self, caller, callee):

        request = {"type": "function", "func_name": "test_rpc", "args": {"host": callee[0], "port": callee[1]}, "response": False}
        response = self.send_request(request, *caller)
        return response

    def send_request(self, request, host, port):
        while True:
            #print(f'sending request to {host} {port}')
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.connect((host, port))
                    # Send a request to the server
                    request_data = json.dumps(request).encode('utf-8')
                    request_length = len(request_data)
                    sock.sendall(struct.pack('!I', request_length))
                    sock.sendall(request_data)

                    #print(f"[send_request] sending the request to {host} {port}, waiting for response")
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
                    #print("[send_request] the response is ", response)
                    return response
            except EOFError:
                ##print(f"Client {peername} disconnected")
                sock.close()
                #print('i mean')
            except Exception as e:
                #print(str(e))
                #print('Unhandled exception')
                sleep(5)

    def async_request(self, request, host, port):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socke:
                    socke.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    socke.bind((self.host, 0))
                    socke.listen()
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.connect((host, port))
                        
                        # Make sure the requests location is specified
                        request["asynch"] = (self.host, socke.getsockname()[1]) # the port to async send back to
                        #logging.info(f"Trying socket to {host} {port} binding to {self.host} {socke.getsockname()[1]} {sock} {socke}")
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
                ##print(f"Client {peername} disconnected")
                sock.close()
            except Exception as e:
                #print(str(e))
                #print('Unhandled exception')
                sleep(5)

    def read_nameserver(self):
        counter = 0
        # Retry lookup with exponential time for retries
        while True:
            try:
                #logging.info(f"start read_nameserver")
                conn = http.client.HTTPConnection("catalog.cse.nd.edu", 9097)
                #logging.info(f"HTTP connection")
                conn.request('GET', '/query.json')
                raw = conn.getresponse()
                #logging.info(f"raw is {raw}")
                raw_data = raw.read().decode('utf-8', errors='replace')  # Decode with error replacement
                #logging.info(f"Raw data received: {raw_data}")
                all_projects = json.loads(raw_data)
                #logging.info(f"all projects are {all_projects}")
                collection = []
                for proj in all_projects:
                    if "type" in proj and proj["type"] == "distsys-data-store" and "owner" in proj and proj["owner"] == "kxue2" and "project" in proj and proj["project"] == self.chord_name:
                        collection.append(proj)
                if collection:
                    break
            except KeyboardInterrupt:
                exit(1)
            except Exception as e:
                print(str(e))
                pass
            time.sleep(2**counter)
            counter += 1
            #print('Attempting reconnect to name server...')
        latest = defaultdict(int)
        name_server = {self.chord_name: {}}
        for entry in collection:
            if entry["lastheardfrom"] > latest[entry["nodeid"]]:
                latest[entry["nodeid"]] = entry["lastheardfrom"]
                name_server[self.chord_name][entry["nodeid"]] = (entry["name"], entry["port"])
        return name_server