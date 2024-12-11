kubectl delete -f client-deployment.yaml

docker build -t client_image .

docker tag client_image lukewarm3/client_image:latest
docker push lukewarm3/client_image:latest

kubectl apply -f client-deployment.yaml
kubectl get pods