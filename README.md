If you want to test, in the outside directory, run in module mode
```bash
python3 -m dds.testing.node1
python3 -m dds.testing.node2
python3 -m dds.testing.node3
python3 -m dds.testing.node4
python3 -m dds.testing.client1
python3 -m dds.testing.node7
python3 -m dds.testing.node5
```
In separate terminals.

Notice that nodes 1-4 just create a nice ring and join, then client1 adds some values, then node7 joins the chord, and node5 prints the contents of all nodes. Node7 joining should cause a value transfer. Observe fingertables and successors/predecessors. Should be correct.

### Initialize the server
build the docker image
```bash
docker build -t node_server_image .
```

tag and push it to the docker hub <br>
```bash
docker tag node_server_image lukewarm3/node_server_image:latest
docker push lukewarm3/node_server_image:latest
```  

push a new version of image to the hub and tag it as the new lastest
```bash
docker build -t lukewarm3/node_server_image:<new-tag> .
docker tag lukewarm3/node_server_image:<new-tag> lukewarm3/node_server_image:latest
docker push lukewarm3/node_server_image:<new-tag>
docker push lukewarm3/node_server_image:latest
```

Apply the bootstrap node deployment, additional node deployment, and the horizontal pod autoscaler yaml file
```bash
kubectl apply -f node-deployment.yaml

kubectl apply -f hpa.yaml

// Simulate high CPU load on one pod to trigger autoscaling
kubectl exec -it <pod_name> -- stress --cpu 2
```

Useful commands
```bash
// inspect the running container interactively
kubectl exec -it <pod_name> -- /bin/sh

// stop the k8 deployment
kubectl delete -f deployment.yaml

// confirm the pods are running
kubectl get pods

// see the print statement in the pod
kubectl logs <pod_name>

// describe the deployment
kubectl describe deployment nodes

// describe the deployment of the pod
kubectl describe pod <pod-name>

```