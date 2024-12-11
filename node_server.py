import os
import hashlib
import logging
import http
import json
import socket
import struct
from time import sleep
from Node import Node # Assuming your Node class is in node_module
import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
# from kubernetes.client import ApiClient
# from kubernetes.client.apis import metrics_v1beta1_api

logging.basicConfig(level=logging.INFO)

def check_if_bootstrap():
    while True:
        try:
            conn = http.client.HTTPConnection("catalog.cse.nd.edu", 9097)
            conn.request('GET', '/query.json')
            raw = conn.getresponse()
            all_projects = json.loads(raw.read().decode('utf-8'))
            for proj in all_projects:
                if "type" in proj and proj["type"] == "distsys-data-store" and "owner" in proj and proj["owner"] == "kxue2" and "project" in proj and proj["project"] == chord_name:
                    # we find one node in the name server
                    return False
            return True
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            logging.info(str(e))
            pass

def get_ip(pod_name):
    while True:
        try:
            conn = http.client.HTTPConnection("catalog.cse.nd.edu", 9097)
            conn.request('GET', '/query.json')
            raw = conn.getresponse()
            all_projects = json.loads(raw.read().decode('utf-8'))
            for proj in all_projects:
                if "type" in proj and proj["type"] == "distsys-data-store" and "owner" in proj and proj["owner"] == "kxue2"\
                      and "project" in proj and proj["project"] == chord_name and "pod_name" in proj and proj["pod_name"] == pod_name:
                    return (proj["host"], proj["port"])
            return None
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            logging.info(str(e))

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

            #logging.info(f"[send_request] sending the request to {host} {port}, waiting for response")
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
            #logging.info("[send_request] the response is ", response)
            return response
        except EOFError:
            #logging.info(f"Client {peername} disconnected")
            sock.close()
            logging.info('i mean')
        except Exception as e:
            logging.info(str(e))
            logging.info('Unhandled exception')
            sleep(5)

def get_pod_cpu_usage(threshold_percentage=60):
    """
    Get pods exceeding the specified CPU utilization threshold as a percentage.
    """
    largest_load_pod = ""
    largest_load = 0

    try:
        # Query metrics API for pod resource usage
        metrics = metrics_client.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace="default",
            plural="pods"
        )

        for pod in metrics["items"]:
            #logging.info(f"the pod is {pod}")
            pod_name = pod["metadata"]["name"]
            cpu_usage = pod["containers"][0]["usage"]["cpu"]
            pod_cpu_limit = "100m"

            # Convert CPU usage and limit to millicores
            usage_m = convert_to_millicores(cpu_usage)
            limit_m = convert_to_millicores(pod_cpu_limit)

            # Calculate utilization
            utilization = (usage_m / limit_m) * 100 if limit_m else 0

            if utilization > largest_load:
                largest_load_pod = pod_name
                largest_load = utilization

            # Check if utilization exceeds threshold
            if utilization > threshold_percentage:
                logging.info(f"Pod {pod_name} exceeds CPU threshold with {utilization}%")
                return pod_name  # Return the first pod exceeding the threshold
            
            # if cannot have the pod that has exceeding load, return the pod that has the largest utilization
            return largest_load_pod

    except ApiException as e:
        print(f"Exception when calling Kubernetes API: {e}")
        return None

def convert_to_millicores(cpu_value):
    """Convert CPU value to millicores."""
    if cpu_value.endswith("n"):  # Nano cores
        return int(cpu_value[:-1]) / 1e6
    elif cpu_value.endswith("m"):  # Millicores
        return int(cpu_value[:-1])
    else:  # Full cores
        return int(cpu_value) * 1000

# Get configuration from environment variables
NODE_IP = os.getenv("NODE_IP")
# Load Kubernetes configuration
try:
    # Use in-cluster configuration for pods
    config.load_incluster_config()
    print("Using in-cluster configuration.")
except:
    # Fallback for local development
    config.load_kube_config()
    print("Using kube-config file.")
metrics_client = client.CustomObjectsApi()

#logging.info(f"the node ip is {NODE_IP}")

if not NODE_IP:
    #logging.info("cannot get node ip")
    exit(1)

POD_NAME = os.getenv("NODE_PORT", "node-abc")
NODE_ID = os.getenv("NODE_ID", 20)        # Default: 20

# CLUSTER_SERVICE_HOST = os.getenv("CLUSTER_SERVICE_HOST", "nodes-service")
# CLUSTER_SERVICE_PORT = int(os.getenv("CLUSTER_SERVICE_PORT", "9000"))

# NODE_PORT is nodes-<random-string>, need to change it to a unique int value
#logging.info(f"the metadata name is {POD_NAME}")
BASE_PORT = 9000
NODE_PORT = BASE_PORT + int(hashlib.md5(POD_NAME.encode()).hexdigest(), 16) % 1000 

chord_name = "ring8"

# check if this is the first node
is_bootstrap = check_if_bootstrap()

# nodes = get_request(CLUSTER_SERVICE_HOST, CLUSTER_SERVICE_PORT)
# is_bootstrap = len(nodes) == 0 # there is no node yet

if is_bootstrap:
    # Create the bootstrap node
    logging.info(f"Starting bootstrap node on {NODE_IP}:{9020} with ID {20}, chord name is {chord_name}")
    
    #node = Node(NODE_HOST, NODE_PORT, 20)
    node = Node(NODE_IP, 9020, 20, POD_NAME, chord_name)
    #post_request(CLUSTER_SERVICE_HOST, CLUSTER_SERVICE_PORT, NODE_IP)
    node.create(chord_name)

    # Start listening
    logging.info(f"The node on {NODE_IP}:{9020} with ID {20} starts listening")

# if this is not the first node, this condition will be executed
else:
    # Join an existing network
    BOOTSTRAP_PORT = int(os.getenv("BOOTSTRAP_PORT", 9020))

    # calculate the new node id for the new joined node
    # first find the node that has exceeding CPU load
    pod_name = get_pod_cpu_usage(threshold_percentage=20)
    if not pod_name:
        exit(1)
    
    result = get_ip(pod_name)
    if result:
        exceeding_node_host, exceeding_node_port = result
    else:
        exit(1)

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

    logging.info(f"Joining bootstrap node at {NODE_IP}:{BOOTSTRAP_PORT} with id {new_nodeId}") # node id is wrong for now
    node = Node(NODE_IP, NODE_PORT, new_nodeId, POD_NAME, chord_name)
    node.join(chord_name)
    #update_hpa_min_replicas(deployment_name="nodes", hpa_name="nodes-autoscaler", namespace="default")

    # Start listening
    logging.info(f"The node on {NODE_IP}:{NODE_PORT} with ID {new_nodeId} starts listening")

node.listen()