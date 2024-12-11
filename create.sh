kubectl delete -f node-deployment.yaml

# Build phase
docker build -t node_server_image .
docker tag node_server_image lukewarm3/node_server_image:latest
docker push lukewarm3/node_server_image:latest
# Apply Kubernetes
kubectl apply -f node-deployment.yaml
kubectl apply -f hpa.yaml
kubectl apply -f metrics-role.yaml
kubectl get pods