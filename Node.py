import socket
import select
import struct
import json
import time
import hashlib
from collections.abc import Iterable
import os
import time
import ast  # For safely evaluating strings like "[1, 2, 3]"
import signal
import http.client

'''
Structure of requests and responses

1. Value Requests
    type: value
    var_name: The name of the variable
    val: The value to be used (Optional)
    get: True if get, False if set
2. Function Requests
    type: function
    func_name: The function to be invoked
    args: The arguments
    asynch: means request is async, may have data attached (Optional)
3. Value Responses
    val: The value to be returned
    success: True or False,
4. Function Responses
    val: The value to be returned
    success: True or False
'''

mBit = 10

name_server: dict[int, tuple[str, int]] = {
    "KLuke": {
        20: ("127.0.0.1", 9020),
        110: ("127.0.0.1", 9110),
        200: ("127.0.0.1", 9200),
        290: ("127.0.0.1", 9290),
        900: ("127.0.0.1", 9900)
    }
}

name_of_chord = None
name_of_port = None
nodeid_global = None

nameserver_json_gen = lambda project, port, nodeid: {
        "type": "distsys-data-store",
        "owner": nodeid,
        "port": port,
        "project": project,
        "width": 120,
        "height": 16
    }

def read_nameserver(name):
    counter = 0
    # Retry lookup with exponential time for retries
    while True:
        try:
            conn = http.client.HTTPConnection("catalog.cse.nd.edu", 9097)
            conn.request('GET', '/query.json')
            raw = conn.getresponse()
            all_projects = json.loads(raw.read().decode('utf-8'))
            collection = []
            for proj in all_projects:
                if proj["type"] == "distsys-data-store" and proj["project"] == name:
                    collection.append(proj)
            if collection:
                break
        except KeyboardInterrupt:
            exit(1)
        except:
            pass
        time.sleep(2**counter)
        counter += 1
        print('Attempting reconnect to name server...')
    latest = 0
    newest = None
    for entry in collection:
        if entry["lastheardfrom"] > latest:
            latest = entry["lastheardfrom"]
            newest = entry
    return newest

def send_to_nameserver(signum, frame):
    if name_of_port:
        name_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = nameserver_json_gen(name_of_chord, name_of_port, nodeid_global)
        name_server_socket.sendto(json.dumps(payload).encode('utf-8'), ("catalog.cse.nd.edu", 9097))
        name_server_socket.close()


class Node:

    def __init__(self, host: str, port: int, nodeId: int, name_server: str = "KLuke"):
        self.host = host
        self.port = port
        self.master_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.master_sock.bind((self.host, self.port))
        self.master_sock.listen()
        self.name_server = name_server
        self.host_port_to_sock: dict[tuple[str, int], socket.socket] = {} # map host/port tuple to a socket
        self.sock_to_host_port: dict[socket.socket, tuple[str, int]] = {}
        global name_of_chord
        global name_of_port
        global nodeid_global
        name_of_chord = name_server
        name_of_port = port
        nodeid_global = nodeId

        self.func = {}
        self.func['find_successor'] = self.find_successor # locates the successor of a given node
        self.func['find_predecessor'] = self.find_predecessor # locates the predecessor of a given node
        self.func['create']         = self.create # advertises a new chord to the nameserver
        self.func['join']           = self.join # invocated by a node to join the server, handles the finger table fixes and the stabilization algorithm
        self.func["send_items"] = self.send_items
        self.func['request_items'] = self.request_items
        self.func['confirm_items'] = self.confirm_items
        self.func['delete_items'] = self.delete_items

    #   self.func['leave']
        # For testing purposes
        self.func['test_rpc'] = self.test_rpc
        self.func['lame_request'] = self.lame_request
        # Important Data Structures
        self.fingerTable = [None] * mBit # succ(2^i) where i is the index
        self.nodeId = nodeId
        self.host = host
        self.port = port
        self.successor = None
        self.predecessor = None
        self.storage = {}
        self.ring_name = None

        # checkpoint and logging
        self.logSize = 0
        self.logFile = open("sheet.log", "a")
        #self._recover()

    def read_and_respond(self, block=True):
        if block:
            readable, _, _ = select.select(list(self.host_port_to_sock.values()) + [self.master_sock], [], [])
        else:
            # the function will perform a non-blocking check
            readable, _, _ = select.select(list(self.host_port_to_sock.values()) + [self.master_sock], [], [], 0)
        for sock in readable:
            if sock is self.master_sock:
                connection, addr = sock.accept()
                print(f"new connection from {addr}")
                self.host_port_to_sock[addr] = connection
                self.sock_to_host_port[connection] = addr
            else:
                try:
                    length_header = b''
                    while len(length_header) < 4:
                        chunk = sock.recv(4 - len(length_header))
                        if not chunk:
                            raise EOFError("Socket connection broken")
                        length_header += chunk
                    m_length = struct.unpack('!I', length_header)[0]
                    request = sock.recv(m_length)
                    
                    # get the remote request in json format
                    request = json.loads(request.decode('utf-8'))
                    response = {}
                    # 2 types: value => request for value update
                    # function => request to format some action
                    print(request)
                    if request['type'] == 'value':
                        response = self.handle_value_request(request)      
                    elif request['type'] == 'function':
                        func_name = request['func_name']
                        args = request['args']
                        if "asynch" in request:
                            args["asynch"] = request["asynch"]
                        response = self.func[func_name](**args)
                        print(f"sending back response of {response} from {func_name} {sock.getpeername()}")
                    if "asynch" not in request: # only send response back if "asynch" not in it
                        print("async not in request")
                        # queue the response, do not send it back yet
                        response_data = json.dumps(response).encode('utf-8')
                        response_length = len(response_data)
                        #response_queue[sock] = response_length + response_data  # Queue data to send

                        sock.sendall(struct.pack('!I', response_length))
                        sock.sendall(response_data)
                        
                except EOFError:
                    #print(f"Client {peername} disconnected")
                    sock.close()
                    del self.host_port_to_sock[self.sock_to_host_port[sock]]
                    del self.sock_to_host_port[sock]
                except OSError as e:
                    if e.errno == 9:
                        # Ignore the Bad File Descriptor error
                        pass  # Simply pass to ignore the error
                except (ConnectionResetError, BrokenPipeError) as e:
                    #print(f"Client {peername} disconnected unexpectedly: {e}")
                    pass
                except json.JSONDecodeError:
                    pass
                    #print(f"Received malformed JSON from {peername}")

    def handle_value_request(self, request):
        requested = request["var_name"]
        get = request["get"]
        response = {}
        response['success'] = True
        if requested == "all":
            response["val"] = [
                self.fingerTable,
                self.nodeId,
                self.host,
                self.port,
                self.successor,
                self.predecessor,
                self.storage,
                self.ring_name,
            ]
        elif requested == "successor":
            if get:
                response["val"] = self.successor
            else:
                self.successor = request["val"]
                self.add_to_log("successor", request["val"])
        elif requested == "predecessor":
            if get:
                response["val"] = self.predecessor
            else:
                self.predecessor = request["val"]
                self.add_to_log("predecessor", request["val"])
        elif requested == "fingerTable":
            if get:
                response["val"] = self.fingerTable
            else:
                self.fingerTable = request["val"]
                self.add_to_log("fingerTable", request["val"])
        elif requested == 'storage': 
            if get:
                response["val"] = self.storage[request["val"]]
            elif request["val"][0] == "RESTRICTED_FOR_DELETE0x0x0":
                del self.storage[request["val"][1]]
                self.add_to_log("storage", request["val"][1], "delete")
            else:
                self.storage[request["val"][0]] = request["val"][1] # val should look like ("key", "value")
                self.add_to_log("storage", request["val"][0], "update", request["val"][1])
        print("storage", self.storage)
        return response
    
    def listen(self):
        while True:
            self.read_and_respond()
    
    def send_request(self, request, host, port, wait_response=True):
        while True:
            print(f'sending request to {host} {port}')
            try:
                if (host, port) in self.host_port_to_sock:
                    sock = self.host_port_to_sock[(host, port)]
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((host, port))
                    self.host_port_to_sock[(host, port)] = sock
                    self.sock_to_host_port[sock] = (host, port)
                # Send a request to the server
                request_data = json.dumps(request).encode('utf-8')
                request_length = len(request_data)
                sock.sendall(struct.pack('!I', request_length))
                sock.sendall(request_data)

                print(f"[send_request] sending the request to {host} {port}, waiting for response")
                # set a time out for receiving message
                sock.settimeout(5)
                # Receive the response from the server
                if "asynch" not in request:
                    length_header = b''
                    while len(length_header) < 4:
                        chunk = sock.recv(4 - len(length_header))
                        length_header += chunk
                    m_length = struct.unpack('!I', length_header)[0]
                    response = sock.recv(m_length)
                    response = json.loads(response.decode('utf-8'))
                    print("[send_request] the response is ", response)
                    return response
                else:
                    return None

            except EOFError:
                #print(f"Client {peername} disconnected")
                sock.close()
                del self.host_port_to_sock[self.sock_to_host_port[sock]]
                del self.sock_to_host_port[sock]
            except Exception as e:
                print(str(e))
                print('Unhandled exception')
            finally:
                self.read_and_respond(block=False)
                
    
    '''
    Everything here and below are functions that the node can execute on behalf of requests it receives
    The first node that initialize the request will use async_request() because it can return the response back
    It will attach "asynch" into the request, so the send_request() called by other nodes will not be blocked
    '''

    def async_request(self, request, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socke:
            socke.bind((self.host, 0))
            socke.listen()
            while True:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((host, port))
                    # Make sure the requests location is specified
                    request["asynch"] = (self.host, socke.getsockname()[1]) # the port to async send back to
                    request_data = json.dumps(request).encode('utf-8')
                    request_length = len(request_data)
                    sock.sendall(struct.pack('!I', request_length))
                    sock.sendall(request_data)
                    # set a time out for receiving message
                    socke.setblocking(False)
                    
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
                            self.read_and_respond(block=False)
                            

                except EOFError:
                    #print(f"Client {peername} disconnected")
                    sock.close()
                    del self.host_port_to_sock[self.sock_to_host_port[sock]]
                    del self.sock_to_host_port[sock]
                except Exception as e:
                    print(str(e))
                    print('Unhandled exception')
                finally:
                    self.read_and_respond(block=False)
                    
    def send_items(self, hash_range):
        transfer = {}
        for key in self.storage:
            key_hash = hash_it(key) % 2**mBit
            # do not pop data now because the transfer message may not be sent back successfully
            # if pop it now, the data can be lost forever. the requester will later send a confirmation message to confirm that it has received the data
            if between_inc_inc(hash_range[0], hash_range[1], key_hash): 
                transfer[key] = self.storage[key]
        response = {"val": transfer, "success": True}
        return response
    
    def request_items(self, host, port, hash_range):
        request = {"type": "function", "func_name": "send_items", "args": {"hash_range": hash_range}}
        response = self.send_request(request, host, port)
        return response
    
    def delete_items(self, hash_range):
        for key in self.storage.copy():
            key_hash = hash_it(key) % 2**mBit
            # do not pop data now because the transfer message may not be sent back successfully
            # if pop it now, the data can be lost forever. the requester will later send a confirmation message to confirm that it has received the data
            if between_inc_inc(hash_range[0], hash_range[1], key_hash): 
                del self.storage[key]
        
        response = {"success": True}
        return response

    def confirm_items(self, host, port, hash_range):
        request = {"type": "function", "func_name": "delete_items", "args": {"hash_range": hash_range}}
        response = self.send_request(request, host, port)
        return response

    def lame_request(self):
        '''
        Returns a test response to test whether test_rpc can work. In conjunction with
        test_rpc, can be used to test interleaved requests between two nodes. Callable
        from the client. 
        Parameters:
            None
        Returns:
            A response object of type Function Response
        '''
        return {"val": "IM LAME", "success": True, "response": True}

    def test_rpc(self, host, port):
        '''
        Transfers a lame request to a target specified by host and port. Typically can
        be called through the client to make a dummy request on a second node through
        a first node
        Parameters:
            host (string): The hostname
            port (integer): The port
        returns:
            A response object of type Function Response (result of lame_response)
        '''
        request = {"type": "function", "args": {}, "func_name": "lame_request", "response": False}
        return self.send_request(request, host, port)
    
    def find_successor(self, hash, asynch):  # successor of a node x defined: if node is y and pred(node) = z. If in interval (z, y]
        print('successor function called')
        '''
        Recursively calls additional nodes on fingertable until successor of hash calls find_successor,
        in which case it looks up the requesterID and communicates with it that it is it. Should be remotely
        invoked with a async_request
        Parameters:
            asynch (str, int): requester hostname, requester temp port
            hash (integer): The SHA-256 hash of the data
        returns:
            A response object containing a val object consisting of a hostname, port, and ID
            to identify the successor of the hash
        '''
        print(self.predecessor, self.nodeId, self.successor)
        if between_exc_inc(self.predecessor, self.nodeId, hash):
            response = {}
            response = {"success": True, "val": {"port": self.port, "hostname": self.host, "nodeid": self.nodeId}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socke:
                socke.connect(tuple(asynch))
                response_data = json.dumps(response).encode('utf-8')
                request_length = len(response_data)
                socke.sendall(struct.pack('!I', request_length))
                socke.sendall(response_data)
            return None
        elif between_exc_inc(self.nodeId, self.successor, hash):
            response = {}
            response = {"success": True, "val": {"port": "PLACEHOLDER", "hostname": "PLACEHOLDER", "nodeid": self.successor}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socke:
                socke.connect(tuple(asynch))
                response_data = json.dumps(response).encode('utf-8')
                request_length = len(response_data)
                socke.sendall(struct.pack('!I', request_length))
                socke.sendall(response_data)
            return None
        else:
            for i in range(len(self.fingerTable) + 1):
                if i < len(self.fingerTable) and i >= 0:
                    ft_i_id = self.fingerTable[i]
                if i == len(self.fingerTable) or (ft_i_id is not None and ft_i_id in name_server[self.name_server].keys() and between_exc_inc(self.nodeId, self.fingerTable[i], hash)):
                    args = {'hash': hash}
                    host, port = name_server[self.name_server][self.fingerTable[i-1 if i >= 1 else 0]]
                    request = {"type": "function", "func_name": "find_successor", "args": args, "asynch": asynch}
                    response = self.send_request(request, host, port)
                    return response

    def find_predecessor(self, hash, asynch):
        print(hash)
        if between_inc_exc(self.nodeId, self.successor, hash):
            print(self.nodeId, self.successor, hash)
            response = {}
            response = {"success": True, "val": {"port": self.port, "hostname": self.host, "nodeid": self.nodeId}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socke:
                print(asynch)
                socke.connect(tuple(asynch))
                response_data = json.dumps(response).encode('utf-8')
                request_length = len(response_data)
                socke.sendall(struct.pack('!I', request_length))
                socke.sendall(response_data)
            return None
        if between_inc_exc(self.predecessor, self.nodeId, hash):
            response = {}
            response = {"success": True, "val": {"port": "PLACEHOLDER", "hostname": "PLACEHOLDER", "nodeid": self.predecessor}}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socke:
                print(asynch)
                socke.connect(tuple(asynch))
                response_data = json.dumps(response).encode('utf-8')
                request_length = len(response_data)
                socke.sendall(struct.pack('!I', request_length))
                socke.sendall(response_data)
            return None
        else:
            for i in range(len(self.fingerTable) + 1):
                if i < len(self.fingerTable) and i >= 0:
                    ft_i_id = self.fingerTable[i]
                if i == len(self.fingerTable) or (ft_i_id is not None and ft_i_id in name_server[self.name_server].keys() and between_inc_exc(self.nodeId, self.fingerTable[i], hash)):
                    print(i)
                    args = {'hash': hash}
                    not_found = False
                    if self.fingerTable[i-1 if i >= 1 else 0] != None:
                        host, port = name_server[self.name_server][self.fingerTable[i-1 if i >= 1 else 0]] 
                    else:
                        not_found = True
                    if not_found or (host, port) == (self.host, self.port):
                        host, port = name_server[self.name_server][self.predecessor]
                    print(self.predecessor)
                    request = {"type": "function", "func_name": "find_predecessor", "args": args, "asynch": asynch}
                    response = self.send_request(request, host, port)
                    return response

        #type: function
        #func_name: The function to be invoked
        #args: The arguments
        #asynch: the host and port to send to

    
    def create(self, name = "KLuke"):
        '''
        Creates an entry in the Notre Dame nameserver that is the name of our new Chord node
        Parameters:
            name (string): The name desired
        returns:
            A response of type Function Response indicaing success/failure
        '''
        # TODO: Advertise to nameserver

        self.successor = self.nodeId
        self.add_to_log("successor", self.nodeId)
        self.predecessor = self.nodeId
        self.add_to_log("predecessor", self.nodeId)
        self.fingerTable = [None] * mBit
        self.ring_name = name
        self.add_to_log("ring_name", self.ring_name)

        signal.signal(signal.SIGALRM, send_to_nameserver)
        signal.setitimer(signal.ITIMER_REAL, 0.1, 60)



    def join(self, name = "KLuke"):
        '''
        Invocated by the node joining the Chord. Updates the corresponding attributes
        and issues requests for other Nodes to also update
        Parameters:
            name (string): The name of the nameserver
        Returns:
            A response of type Function Response indicating success/failure
        '''
        # TODO: Request a random node from nameserver
        random_node = name_server[name][20]
        '''
        The following updates the successor and predecessor pointers and the successor's predecessor and predecessor's successor
        '''
        request = {"type": "function", "func_name": "find_successor", "args": {"hash": self.nodeId}}
        response = self.async_request(request, *random_node) # this find's the successor which is this node's successor
        print(response)
        if response["success"] == True:
            self.successor = response["val"]["nodeid"]
            self.add_to_log("successor", response["val"]["nodeid"])
        pred_request = {"type": "value", "var_name": "predecessor", "get": True} # this finds the successor's predecessor which is now this node's predecessor
        response = self.send_request(pred_request, *name_server[name][self.successor])
        if response["success"] == True:
            print(response)
            self.predecessor = response["val"]
            self.add_to_log("predecessor", response["val"])
        update_request = {"type": "value", "var_name": "predecessor", "get": False, "val": self.nodeId} # this makes the successor's predecessor this node
        response = self.send_request(update_request, *name_server[name][self.successor])

        update_request = {"type": "value", "var_name": "successor", "get": False, "val": self.nodeId} # this makes the current node's predecessor's successor this node
        response = self.send_request(update_request, *name_server[name][self.predecessor])
        '''
        Update the predecessor for all nodes
        '''
        # Then update other fingertables
        for i in range(len(self.fingerTable)):
            # find the predecessor
            request = {"type": "function", "func_name": "find_predecessor", "args": {"hash": (self.nodeId - 2**i) % 2**mBit}}
            print('ndid', self.nodeId - 2**i)
            response = self.async_request(request, *random_node)
            predecessor = response["val"]["nodeid"]
            print(predecessor)
            while True:
                if predecessor == self.nodeId:
                    break
                # get its fingerTable
                # if finger table entry at i is less than node, then pass
                request = {"type": "value", "var_name": "fingerTable", "get": True}
                response = self.send_request(request, *name_server[name][predecessor])
                curr_val = response["val"][i]
                if curr_val != None and not between_inc_exc((predecessor + 2**i) % 2**mBit, curr_val, self.nodeId):
                    break
                else: # else, update it and also try the predecessor of that
                    new_ft = response["val"]
                    new_ft[i] = self.nodeId
                    request = {"type": "value", "var_name": "fingerTable", "val": new_ft, "get": False}
                    response = self.send_request(request, *name_server[name][predecessor])
                    request = {"type": "value", "var_name": "predecessor", "get": True}
                    response = self.send_request(request, *name_server[name][predecessor])
                    predecessor = response["val"]
                    
        # first update own fingertable
        for i in range(len(self.fingerTable)):
            node_q = (self.nodeId + 2**i) % 2**mBit
            if between_exc_inc(self.nodeId, self.successor, node_q):
                self.fingerTable[i] = self.successor
                self.add_to_log("fingerTable", self.fingerTable)
            else:
                request = {"type": "function", "func_name": "find_successor", "args": {"hash": node_q}}
                print((self.nodeId + 2**i) % 2**mBit)
                response = self.async_request(request, *random_node)
                self.fingerTable[i] = response["val"]["nodeid"]
                self.add_to_log("fingerTable", self.fingerTable)
                print(response)
        print('ft', self.fingerTable)

        # Finally, handle transfer over to this node
        response = self.request_items(*name_server[name][self.successor], (self.predecessor + 1, self.nodeId))
        if response["success"] == True:
            print(response["val"])
            for key, value in response["val"].items():
                self.storage[key] = value
                self.add_to_log("storage", key, "update", value)
  
        # send the confirmation message to the successor to confirm that it has received the new data
        response = self.confirm_items(*name_server[name][self.successor], (self.predecessor + 1, self.nodeId))
        if response["success"] == True:
            print("confirm message successfully")

        # let the nameserver know that this node now exists
        signal.signal(signal.SIGALRM, send_to_nameserver)
        signal.setitimer(signal.ITIMER_REAL, 0.1, 60)
        
        new_response = {"success": True, "val": None}

        return new_response
    
    def _recover(self):
        if os.path.exists("sheet.ckpt"):
            with open("sheet.ckpt", "r") as file:
                checkpoint = json.load(file)
                self.fingerTable = json.loads(checkpoint["fingerTable"])
                self.successor = int(checkpoint["successor"])
                self.predecessor = int(checkpoint["successor"])
                self.ring_name = checkpoint["ring_name"]

                json_storage = checkpoint["storage"]
                storage = {}
                for key, value in json_storage.items():
                    try:
                        original_key = ast.literal_eval(key)
                    except:
                        original_key = key
                    
                    storage[original_key] = value
                
                self.storage = storage
        
        if os.path.exists("sheet.log"):
            with open("sheet.log", "r") as file:
                for line in file:
                    self.logSize += 1
                    operations = line.split(",")
                    attribute = operations[0]
                    value = operations[1]
                    action = operations[2]
                    key_value = operations[3]
                    if attribute == "fingertable":
                        self.fingerTable = json.loads(value)
                    elif attribute == "successor":
                        self.successor = int(value)
                    elif attribute == "predecessor":
                        self.predecessor = int(value)
                    elif attribute == "ring_name":
                        self.ring_name = value
                    elif attribute == "storage":
                        # the value is string now, convert it to corresponding type of key
                        try:
                            original_key = ast.literal_eval(value)
                        except:
                            original_key = value

                        if action == "delete":
                            del self.storage[original_key]
                        elif action == "update":
                            try:
                                original_value = ast.literal_eval(key_value)
                            except:
                                original_value = key_value
                            self.storage[original_key] = original_value
                    else:
                        print("unknow method in the transaction log: ", attribute)

    # if the attribute is storage, then action can be delete or update, and key_value is the value of the key when action is update
    def add_to_log(self, attribute, value, action=None, key_value=None):
        self.logFile.write(f"{attribute},{value},{action},{key_value},{time.time()}\n")
        self.logFile.flush()
        os.fsync(self.logFile.fileno())
        self.logSize += 1

        self.compact()
    
    def compact(self):
        if self.logSize == 100:
            with open("sheet.ckpt.new", "w") as file:
                checkpoint_new = {}
                checkpoint_new["fingerTable"] = self.fingerTable
                checkpoint_new["successor"] = self.successor
                checkpoint_new["predecessor"] = self.predecessor
                json_storage = {}
                for key, value in self.storage.items():
                    json_storage[str(key)] = value # the key can be iterable, not string or int
                checkpoint_new["storage"] = json_storage
                checkpoint_new["ring_name"] = self.ring_name
                json.dump(checkpoint_new, file)
                file.flush()
                os.fsync(file.fileno())
            
            if os.path.exists("sheet.ckpt"):
                os.remove("sheet.ckpt")
            os.rename("sheet.ckpt.new", "sheet.ckpt")
            if os.path.exists("sheet.log"):
                os.remove("sheet.log")
            self.logFile = open("sheet.log", "a")

            self.logSize = 0

def between_inc_inc(ID1, ID2, key):
    if ID1 == ID2:
        return True
    wrap = ID1 > ID2
    if not wrap:
        return True if key >= ID1 and key <= ID2 else False
    else:
        return True if key >= ID1 or  key <= ID2 else False

def between_inc_exc(ID1, ID2, key): # inclusive, exclusive [)
    if ID1 == ID2:
        return True
    wrap = ID1 > ID2
    if not wrap:
        return True if key >= ID1 and key < ID2 else False
    else:
        return True if key >= ID1 or  key < ID2 else False
    
def between_exc_inc(ID1, ID2, key): # inclusive, exclusive (]
    if ID1 == ID2:
        return True
    wrap = ID1 > ID2
    if not wrap:
        return True if key > ID1 and key <= ID2 else False
    else:
        return True if key > ID1 or key <= ID2 else False
    
def hash_it(obj): # currently can only hash ints and floats and tuples, returns raw int
    if isinstance(obj, int) or isinstance(obj, str):
        if isinstance(obj, int):
            bytes = struct.pack('>I', obj)
        else:
            bytes = obj.encode('utf-8')
        hash_obj = hashlib.sha256()
        hash_obj.update(bytes)
        hex_string = hash_obj.hexdigest()
        hash_val = int(hex_string, 16)
        print(f"hash of {obj}", hash_val % 1024)
        return hash_val
    if isinstance(obj, Iterable):
        total = 0
        for ele in obj:
            if isinstance(ele, int) or isinstance(ele, str):
                hash_num = hash_it(ele)
                total += hash_num
            else:
                print("Contained element is not hashable")
                return None
        return total
    else:
        print("Key is not hashable")
        return None


        
