# jenkins-consul-friends

## Requirements

Kubernetes development cluster (microk8s, minikube, kops, eks, gks, aks, etc.)

Terraform v1.0.1+

Python 3.8+

## Running

You could set the next environment variables:
* JENKINS_UI_PORT
* JENKINS_AGENT_PORT
* CONSUL_UI_PORT
* CONSUL_DNS_PORT"



```
pip install -r requirements.txt
python run.py ~/.kube/config-of-k8s-development-cluster
```

## Particularities

The code doesn't handle resource clean up in case of incorrect termination or restart.