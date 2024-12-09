import os
import hashlib
import logging
from Node import Node # Assuming your Node class is in node_module

logging.basicConfig(level=logging.INFO)

# Get configuration from environment variables
NODE_HOST = os.getenv("NODE_HOST", "127.0.0.1")
NODE_PORT = os.getenv("NODE_PORT", 9020)  # Default: 9020
NODE_ID = os.getenv("NODE_ID", 20)        # Default: 20

logging.info(f"testing")
logging.info(f"Starting bootstrap node on {NODE_HOST}:{NODE_PORT} with ID {NODE_ID}")

# check if this is the first node
# TODO
is_bootstrap = True
if is_bootstrap:
    # Create the bootstrap node
    logging.info(f"Starting bootstrap node on {NODE_HOST}:{NODE_PORT} with ID {NODE_ID}")
    node = Node(NODE_HOST, int(NODE_PORT), int(NODE_ID))
    node.create()
# if this is not the first node, this condition will be executed
else:
    # Join an existing network
    BOOTSTRAP_PORT = int(os.getenv("BOOTSTRAP_PORT", 9020))
    logging.info(f"Joining bootstrap node at {NODE_HOST}:{BOOTSTRAP_PORT}")

    # NODE_PORT now is just a unique pod name. convert the NODE_PORT to a unique port
    logging.info("the unique pod name is ", NODE_PORT)
    BASE_PORT = 9000
    NODE_PORT = BASE_PORT + int(hashlib.md5(NODE_PORT.encode()).hexdigest(), 16) % 1000  

    # calculate the new node id for the new joined node
    # first find the node that has exceeding CPU load

    logging.info(f"Starting additional node on {NODE_HOST}:{NODE_PORT} with ID {NODE_ID}") # node id is wrong for now
    node = Node(NODE_HOST, NODE_PORT, NODE_ID)
    node.join()

# Start listening
node.listen()