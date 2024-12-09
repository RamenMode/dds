import os
import hashlib
import logging
import http
import json
import socket
import struct
from Node import Node # Assuming your Node class is in node_module

logging.basicConfig(level=logging.INFO)

def check_if_bootstrap():
    try:
        conn = http.client.HTTPConnection("catalog.cse.nd.edu", 9097)
        conn.request('GET', '/query.json')
        raw = conn.getresponse()
        all_projects = json.loads(raw.read().decode('utf-8'))
        for proj in all_projects:
            if "type" in proj and proj["type"] == "distsys-data-store" and "owner" in proj and proj["owner"] == "kxue2" and "project" in proj and proj["project"] == chord_name:
                # we find one node in the name server
                return False
            
    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        print(str(e))
        pass
    
    return True

def send_request(request, host, port):
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

# Get configuration from environment variables
NODE_HOST = os.getenv("NODE_HOST", "127.0.0.1")
NODE_PORT = os.getenv("NODE_PORT", "nodes-abc123") 
NODE_ID = os.getenv("NODE_ID", 20)        # Default: 20

# NODE_PORT is nodes-<random-string>, need to change it to a unique int value
BASE_PORT = 9000
NODE_PORT = BASE_PORT + int(hashlib.md5(NODE_PORT.encode()).hexdigest(), 16) % 1000 

chord_name = "ring7"

logging.info(f"testing")
logging.info(f"Starting bootstrap node on {NODE_HOST}:{NODE_PORT} with ID {NODE_ID}")

# check if this is the first node
is_bootstrap = check_if_bootstrap()

if is_bootstrap:
    # Create the bootstrap node
    logging.info(f"Starting bootstrap node on {NODE_HOST}:{NODE_PORT} with ID {NODE_ID}")
    
    #node = Node(NODE_HOST, NODE_PORT, 20)
    node = Node(NODE_HOST, 9020, 20)
    node.create()
# if this is not the first node, this condition will be executed
else:
    # Join an existing network
    BOOTSTRAP_PORT = int(os.getenv("BOOTSTRAP_PORT", 9020))
    logging.info(f"Joining bootstrap node at {NODE_HOST}:{BOOTSTRAP_PORT}")

    # NODE_PORT now is just a unique pod name. convert the NODE_PORT to a unique port
    logging.info("the unique pod name is ", NODE_PORT)

    # calculate the new node id for the new joined node
    # first find the node that has exceeding CPU load
    # TODO
    exceeding_node_host = NODE_HOST
    exceeding_node_port = 9020
    # fake_exceeding_node_port = 'nodes-2'
    # exceeding_node_port = BASE_PORT + int(hashlib.md5(fake_exceeding_node_port.encode()).hexdigest(), 16) % 1000

    request = {"type": "value", "var_name": "all", "get": True}
    response = send_request(request, exceeding_node_host, exceeding_node_port)
    predecessor = response["val"][5] # exceeding node's predecessor
    nodeId = response["val"][1] # exceeding node's id

    if predecessor < nodeId:
        new_nodeId = (nodeId + predecessor) // 2
    else:
        new_nodeId = (nodeId + predecessor + 1024) // 2 # suppose the max chord id is 1024

    logging.info(f"Starting additional node on {NODE_HOST}:{NODE_PORT} with ID {NODE_ID}") # node id is wrong for now
    node = Node(NODE_HOST, NODE_PORT, new_nodeId)
    node.join()

# Start listening
node.listen()