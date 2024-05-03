#!/bin/bash

# Set project variables
source ./config.sh

CCA_PROJECT_PUB_KEY=${CCA_PROJECT_PUB_KEY::-4} #Remove .pub
if [[ "$CCA_PROJECT_PUB_KEY" == *.pub ]]; then
    echo "Path to the SSH key ends with .pub. In this case, remove it!"
    exit 1
fi

if [ "$CCA_PROJECT_PUB_KEY" == "$DEFAULT_CCA_PROJECT_PUB_KEY" ]; then
    echo "SSH PUB KEY value is still the placeholder one. Change it!"
    exit 1
fi

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

MEMCACHE_SERVER_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep memcache-server`
echo "#############################################"
echo "# RETRIEVING MEMCACHE IP ADDR"
MEMCACHE_IPADDR=`kubectl get nodes $MEMCACHE_SERVER_NAME -o custom-columns='INTERNAL_IP:.status.addresses[?(@.type=="InternalIP")].address' | head -2 | tail -1`
echo "# ADDR: $MEMCACHE_IPADDR"
echo "#############################################"

echo "#############################################"
echo "# DEPLOYING ON $MEMCACHE_SERVER_NAME"
echo "#############################################"
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY remote_setup_memcache.sh "ubuntu@$MEMCACHE_SERVER_NAME:/home/ubuntu/remote_setup_memcache.sh" --zone europe-west3-a
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "cd /home/ubuntu && chmod 744 remote_setup_memcache.sh && ./remote_setup_memcache.sh $MEMCACHE_IPADDR"
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY get_cpu.py "ubuntu@$MEMCACHE_SERVER_NAME:/home/ubuntu/get_cpu.py" --zone europe-west3-a