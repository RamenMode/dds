## Simple Test of the Chord without Loading Balancing
**Important**
please ensure if running without k8s that this line is changed in the read_nameserver function across all RingClient.py and Node.py files
```python3
name_server[self.chord_name][entry["nodeid"]] = (entry["name"], entry["port"]) # should be "name" for base python, "host" for k8s run method
```
If you want to test without the feature of load balancing, then in the outside directory, run in module mode
```bash
python3 -m dds.testing.node1
python3 -m dds.testing.node2
python3 -m dds.testing.node3
python3 -m dds.testing.node4
python3 -m dds.testing.groupAnagrams.client2
```
Also make sure the line in read_nameserver(self) in Node.py and RingClinet.py is
```python
name_server[self.chord_name][entry["nodeid"]] = (entry["name"], entry["port"])
```
instead of
```python
name_server[self.chord_name][entry["nodeid"]] = (entry["host"], entry["port"])
```

In separate terminals.

Notice that nodes 1-4 just create a nice ring and join, then client1 adds some values, then node7 joins the chord, and node5 prints the contents of all nodes. Node7 joining should cause a value transfer. Observe fingertables and successors/predecessors. Should be correct.


## Test Chord for Load Balancing
### Initialize the server
run the create.sh file
```bash
./create.sh
```

What it does is: <br>
build the docker image
```bash
docker build -t node_server_image .
```

tag and push it to the docker hub <br>
```bash
docker tag node_server_image lukewarm3/node_server_image:latest
docker push lukewarm3/node_server_image:latest
```  

Apply the node deployment, the horizontal pod autoscaler, and metric yaml file
```bash
kubectl apply -f node-deployment.yaml

kubectl apply -f hpa.yaml

kubectl apply -f metrics-role.yaml

// get the pod name using this command
kubectl get pods
```

Then simulate the stress to see the load balancing feature
```bash
// Simulate high CPU load on one pod to trigger autoscaling
kubectl exec -it <pod_name> -- stress --cpu 2

// see the CPU load of all pods
kubectl top pods

// see if there are more pods now
kubectl get pods
```

Useful commands
```bash
// inspect the running container interactively
kubectl exec -it <pod_name> -- /bin/sh

// stop the k8 deployment
kubectl delete -f node-deployment.yaml

// see the print statement in the pod
kubectl logs <pod_name>

// describe the deployment
kubectl describe deployment nodes

// describe the deployment of the pod
kubectl describe pod <pod-name>

```
## Running the Main System with Kubernetes
NOTE: If rerunning the system in a short interval, you have to change all instancesn of the chord name (in this case, ring24, which is easy to find in VSCode across the entire repo with a different name for discovery via the nameserver)
### Run the Pods
Run the script in the root directory
```bash
./create.sh
```
**Everything past this point is done in a separate terminal**
### Add more pods
Note that the current utilization is set at 50 or 60% in the hpa.yaml file, or the threshold of total CPU that will cause the node to split
#### Method 1: Simulate stress using the stress module
```bash
kubectl get pods
kubectl exec -it <pod_name> -- stress --cpu <number>
```
This will cause nodes to eventually split. Keep track of them with kubectl get pods
#### Method 2: Change parameters in the yaml file and run the actual test
In node-deployment.yaml
```bash
resources:
  requests:
    cpu: '500m' # decrease to lower the number of cores, this is 0.5 cores
  limits:
    cpu: '500m' # decrease to lower the number of cores
```
### Run the test
cd into ./testing
```bash
./create.sh
```
Observe logs by running
```bash
kubectl get pods
kubectl logs <client-node-id>
```


