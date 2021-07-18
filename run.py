import argparse
import logging
import os
import random
import socket
import subprocess
import sys
import tempfile

import requests
import retrying
from kubernetes import client, config
from kubernetes.client.rest import ApiException

WAIT_TIMEOUT_SEC: int = 5 * 60
WAIT_SLEEP_SEC: int = 5

# Initialization & basic validation
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.NOTSET)
logging.getLogger("kubernetes").setLevel(logging.INFO)
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
parser = argparse.ArgumentParser(description='Service discovery and KV store using consul and friend.')
parser.add_argument('kubeconfig', help='Full path to the configuration of the development Kubernetes cluster')
args = parser.parse_args()
config.load_kube_config(config_file=args.kubeconfig)
v1 = client.CoreV1Api()
# It is required because for this demo local volume is used
# Local volumes are required affinity settings
local_volume_node_hostname = ""
try:
    list_nodes = v1.list_node()
    for node in list_nodes.items:
        if node.spec.unschedulable:
            continue
        labels = dict(node.metadata.labels)
        local_volume_node_hostname = labels["kubernetes.io/hostname"]
        break
except Exception as e:
    logger.error("Unable to list namespaces of the current Kubernetes cluster: %s", e, exc_info=1)
    exit(-1)
logger.info("Selected node with kubernetes.io/hostname '%s' for the local volume", local_volume_node_hostname)


def wait_for_statefulset_available_replicas(name,
                                            namespace,
                                            count=1,
                                            timeout_sec=WAIT_TIMEOUT_SEC,
                                            wait_sec=WAIT_SLEEP_SEC):
    def _replicas_available(resource, count):
        return (resource is not None and resource.status.ready_replicas is not None
                and resource.status.ready_replicas >= count)

    @retrying.retry(retry_on_result=lambda r: not _replicas_available(r, count),
                    stop_max_delay=timeout_sec * 1000,
                    wait_fixed=wait_sec * 1000)
    def _wait_for_statefulset_available_replicas():
        statefulset = client.AppsV1Api().read_namespaced_stateful_set(name, namespace)
        logger.debug('Waiting for statefulset %s to have %s available '
                     'replicas, current count %s', statefulset.metadata.name, count, statefulset.status.ready_replicas)
        return statefulset

    logger.info("Waiting for statefulset {}".format(name))
    _wait_for_statefulset_available_replicas()


def run(cmd, dir=".", env=os.environ.copy()):
    logger.info(">>>>>>>> run '{}' at '{}'".format(cmd, dir))
    p = subprocess.Popen(cmd, cwd=dir, shell=True, env=env, stdout=sys.stdout, stderr=sys.stderr)
    p.wait()


def background(cmd, dir="."):
    logger.info(">>>>>>>> spawn '{}' at '{}'".format(cmd, dir))
    return subprocess.Popen(cmd, cwd=dir, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def pick_random_port():
    port = 0
    random.seed()
    for i in range(8):
        port = random.randint(10000, 60000)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if s.connect_ex(('127.0.0.1', port)) == 0:
            s.close()
        else:
            break
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.bind(('127.0.0.1', port))
        except Exception:
            break
        s.close()
    if port == 0:
        logging.error('FAIL')
        sys.exit('Could not find a random free port between 10000 and 60000')
    return port


def download_slave_jar(url, timeout_sec=WAIT_TIMEOUT_SEC, wait_sec=WAIT_SLEEP_SEC):
    @retrying.retry(stop_max_delay=timeout_sec * 1000, wait_fixed=wait_sec * 1000)
    def _download_slave_jar():
        logging.info("download slave.jar from %s", url)
        r = requests.get(url, allow_redirects=True)
        slave_jar_file, slave_jar_filename = tempfile.mkstemp(".jar", "slave_")
        os.write(slave_jar_file, r.content)
        os.close(slave_jar_file)
        logging.info("save to %s", slave_jar_filename)
        return slave_jar_filename

    return _download_slave_jar()

def ping_microservice(url, timeout_sec=WAIT_TIMEOUT_SEC, wait_sec=WAIT_SLEEP_SEC):
    @retrying.retry(stop_max_delay=timeout_sec * 1000, wait_fixed=wait_sec * 1000)
    def _ping_microservice():
        logging.info("ping %s", url)
        r = requests.get(url, allow_redirects=True)
        if r.status_code != 200:
            raise Exception("unreachable")

    _ping_microservice()


print("\n\nYou could set the next environment variables:")
print("JENKINS_UI_PORT")
print("JENKINS_AGENT_PORT")
print("CONSUL_UI_PORT")
print("CONSUL_DNS_PORT")

# Update kubernetes resources
jenkins_ui_port = os.getenv("JENKINS_UI_PORT", pick_random_port())
jenkins_agent_port = os.getenv("JENKINS_AGENT_PORT", pick_random_port())
consul_ui_port = os.getenv("CONSUL_UI_PORT", pick_random_port())
consul_dns_port = os.getenv("CONSUL_DNS_PORT", pick_random_port())

# Terraform
run("terraform init", "./terraform/dev")
terraform_env = os.environ.copy()
terraform_env["TF_VAR_jenkins_ui_port"] = str(jenkins_ui_port)
terraform_env["TF_VAR_jenkins_agent_port"] = str(jenkins_agent_port)
terraform_env["TF_VAR_local_volume_node_hostname"] = local_volume_node_hostname
terraform_env["TF_VAR_consul_ui_port"] = str(consul_ui_port)
terraform_env["TF_VAR_consul_dns_port"] = str(consul_dns_port)
run("terraform apply -auto-approve", "./terraform/dev", terraform_env)

# Kubernetes
wait_for_statefulset_available_replicas("jenkins", "jenkins")
jenkins_ui = background("kubectl -n jenkins port-forward svc/jenkins {}".format(jenkins_ui_port))
jenkins_agent = background("kubectl -n jenkins port-forward svc/jenkins-agent {}".format(jenkins_agent_port))

slave_jar = download_slave_jar("http://localhost:{}/jnlpJars/slave.jar".format(jenkins_ui_port))
slave_connection_url = "http://localhost:{}/computer/localhost/jenkins-agent.jnlp".format(jenkins_ui_port)
jenkins_slave = background("java -jar {} -jnlpUrl {} -jnlpCredentials admin:admin".format(slave_jar, slave_connection_url))

ping_microservice("http://localhost:9003/ping")

print("\n\n\nMicroservice is deployed\n")
print("set keys: curl 'localhost:9003/set-value?b=x&a=y'")
print("get keys: curl 'localhost:9003/get-value?b&a'")
print("Jenkins UI: localhost:{} (admin:admin)".format(jenkins_ui_port))
print("Consul UI: localhost:{}".format(consul_ui_port))
print("Consul DNS: localhost:{}".format(consul_dns_port))
print("test service discovery: dig @localhost -p {} jenkins-consul-friends.service.consul".format(consul_dns_port))

input("Press Enter to finish...\n\n\n")

jenkins_slave.kill()
jenkins_ui.kill()
jenkins_agent.kill()

jenkins_slave.wait()
jenkins_ui.wait()
jenkins_agent.wait()
