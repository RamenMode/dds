import os
import hashlib
import logging
import http
import json
import socket
import struct
from time import sleep
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
        logging.info(str(e))
        pass
    
    return True

def send_request(request, host, port):
    while True:
        logging.info(f'sending request to {host} {port}')
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            # Send a request to the server
            request_data = json.dumps(request).encode('utf-8')
            request_length = len(request_data)
            sock.sendall(struct.pack('!I', request_length))
            sock.sendall(request_data)

            logging.info(f"[send_request] sending the request to {host} {port}, waiting for response")
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
            logging.info("[send_request] the response is ", response)
            return response
        except EOFError:
            #logging.info(f"Client {peername} disconnected")
            sock.close()
            logging.info('i mean')
        except Exception as e:
            logging.info(str(e))
            logging.info('Unhandled exception')
            sleep(5)

# def post_request(cluster_service_host, cluster_service_port, node_ip):
#     # Create the JSON payload
#     payload = json.dumps({"ip": node_ip})

#     # Establish a connection
#     conn = http.client.HTTPConnection(cluster_service_host, cluster_service_port)

#     # Send the POST request
#     headers = {"Content-Type": "application/json"}
#     conn.request("POST", "/register", payload, headers)
#     conn.close()

# def get_request(cluster_service_host, cluster_service_port):
#     # Establish a connection
#     conn = http.client.HTTPConnection(cluster_service_host, cluster_service_port)

#     # Send the GET request
#     conn.request("GET", "/nodes")

#     # Get the response
#     response = conn.getresponse()
#     logging.info(f"GET /nodes: {response.status} {response.reason}")
#     data = response.read().decode()
#     logging.info("Response data:", data)

#     # Parse the JSON response if needed
#     nodes = json.loads(data)
#     logging.info("Nodes:", nodes)

#     # Close the connection
#     conn.close()
#     return nodes

# Get configuration from environment variables
NODE_IP = os.getenv("NODE_IP")

logging.info(f"the node ip is {NODE_IP}")

if not NODE_IP:
    logging.info("cannot get node ip")
    exit(1)

NODE_PORT = os.getenv("NODE_PORT", "node-abc")
NODE_ID = os.getenv("NODE_ID", 20)        # Default: 20

# CLUSTER_SERVICE_HOST = os.getenv("CLUSTER_SERVICE_HOST", "nodes-service")
# CLUSTER_SERVICE_PORT = int(os.getenv("CLUSTER_SERVICE_PORT", "9000"))

# NODE_PORT is nodes-<random-string>, need to change it to a unique int value
BASE_PORT = 9000
NODE_PORT = BASE_PORT + int(hashlib.md5(NODE_PORT.encode()).hexdigest(), 16) % 1000 

chord_name = "ring11"

logging.info(f"testing")

# check if this is the first node
is_bootstrap = check_if_bootstrap()

# nodes = get_request(CLUSTER_SERVICE_HOST, CLUSTER_SERVICE_PORT)
# is_bootstrap = len(nodes) == 0 # there is no node yet

if is_bootstrap:
    # Create the bootstrap node
    logging.info(f"Starting bootstrap node on {NODE_IP}:{9020} with ID {20}, chord name is {chord_name}")
    
    #node = Node(NODE_HOST, NODE_PORT, 20)
    node = Node(NODE_IP, 9020, 20, chord_name)
    #post_request(CLUSTER_SERVICE_HOST, CLUSTER_SERVICE_PORT, NODE_IP)
    node.create(chord_name)
# if this is not the first node, this condition will be executed
else:
    # Join an existing network
    BOOTSTRAP_PORT = int(os.getenv("BOOTSTRAP_PORT", 9020))
    logging.info(f"Joining bootstrap node at {NODE_IP}:{BOOTSTRAP_PORT}")

    # calculate the new node id for the new joined node
    # first find the node that has exceeding CPU load
    # TODO
    exceeding_node_host = NODE_IP

    # Original IP address as a string
    ip_address = exceeding_node_host

    # Split the IP address into parts
    parts = ip_address.split(".")

    # Convert the last part to an integer, decrease by 1, and update
    parts[-1] = str(int(parts[-1]) - 1)

    # Join the parts back into a string
    exceeding_node_host = ".".join(parts)

    exceeding_node_port = 9020
    logging.info(f"sending request to {exceeding_node_host} {exceeding_node_port}")
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

    logging.info(f"register node on {NODE_IP}:{NODE_PORT} with ID {new_nodeId}")
    #post_request(CLUSTER_SERVICE_HOST, CLUSTER_SERVICE_PORT, NODE_IP)

    logging.info(f"Starting additional node on {NODE_IP}:{NODE_PORT} with ID {new_nodeId}") # node id is wrong for now
    node = Node(NODE_IP, NODE_PORT, new_nodeId, chord_name)
    node.join(chord_name)

# Start listening
logging.info(f"The node on {NODE_IP}:{9020} with ID {20} starts listening")
node.listen()