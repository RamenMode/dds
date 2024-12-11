## Simple Test of the Chord without Loading Balancing
If you want to test without the feature of load balancing, then in the outside directory, run in module mode
```bash
python3 -m dds.testing.node1
python3 -m dds.testing.node2
python3 -m dds.testing.node3
python3 -m dds.testing.node4
python3 -m dds.testing.client1
python3 -m dds.testing.node7
python3 -m dds.testing.node5
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
kubectl scale deployment nodes --replicas=2

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

```bash
docker build -t client_image .

docker tag client_image lukewarm3/client_image:latest
docker push lukewarm3/client_image:latest
```