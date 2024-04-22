#!/bin/bash

DEFAULT_CCA_PROJECT_PUB_KEY="~/.ssh/file"

# Change this variables according to your configuration (do not add .pub at the end)
CCA_PROJECT_PUB_KEY="~/.ssh/file"

if [[ "$CCA_PROJECT_PUB_KEY" == *.pub ]]; then
    echo "Path to the SSH key ends with .pub. In this case, remove it!"
    exit 1
fi

if [ "$CCA_PROJECT_PUB_KEY" == "$DEFAULT_CCA_PROJECT_PUB_KEY" ]; then
    echo "SSH PUB KEY value is still the placeholder one. Change it!"
    exit 1
fi

kubectl create -f memcache-t1-cpuset.yaml

kubectl expose pod some-memcached --name some-memcached-11211 \
--type LoadBalancer --port 11211 \
--protocol TCP

sleep 60

kubectl get service some-memcached-11211

kubectl get pods -o wide

echo "#############################################"
echo "# RETRIEVING POD IP ADDR"
POD_IPADDR=`kubectl get pod some-memcached -o custom-columns=IP:status.podIP | head -2 | tail -1`
echo "# ADDR: $POD_IPADDR"
echo "#############################################"

CLIENT_AGENT_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent`
echo "#############################################"
echo "# DEPLOYING ON $CLIENT_AGENT_NAME"
echo "#############################################"
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY remote_setup.sh "ubuntu@$CLIENT_AGENT_NAME:/home/ubuntu/remote_setup.sh" --zone europe-west3-a
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- 'cd /home/ubuntu && chmod 744 remote_setup.sh && ./remote_setup.sh'

CLIENT_MEASURE_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-measure`
echo "#############################################"
echo "# DEPLOYING ON $CLIENT_MEASURE_NAME"
echo "#############################################"
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY remote_setup.sh "ubuntu@$CLIENT_MEASURE_NAME:/home/ubuntu/remote_setup.sh" --zone europe-west3-a
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- 'cd /home/ubuntu && chmod 744 remote_setup.sh && ./remote_setup.sh'