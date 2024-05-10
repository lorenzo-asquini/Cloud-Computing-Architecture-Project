#!/bin/bash

# Create folder for the outputs
mkdir ../part4_2_raw_outputs

logEcho() {
    echo $(date -u) "||| $1"
}

CURRENTEPOCTIME=$(date +%s)
logEcho "Current EPOCH is $CURRENTEPOCTIME"

# Set project variables
source ./config.sh

CCA_PROJECT_PUB_KEY=${CCA_PROJECT_PUB_KEY::-4} #Remove .pub
if [[ "$CCA_PROJECT_PUB_KEY" == *.pub ]]; then
    logEcho "Path to the SSH key ends with .pub. In this case, remove it!"
    exit 1
fi

if [ "$CCA_PROJECT_PUB_KEY" == "$DEFAULT_CCA_PROJECT_PUB_KEY" ]; then
    logEcho "SSH PUB KEY value is still the placeholder one. Change it!"
    exit 1
fi

# Allows running a program remotely infinitely without keeping the connection open
mkdir ~/.screen && chmod 700 ~/.screen
export SCREENDIR=$HOME/.screen

MEMCACHE_SERVER_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep memcache-server`
logEcho "#############################################"
logEcho "# RETRIEVING MEMCACHE IP ADDR"
MEMCACHE_IPADDR=`kubectl get nodes $MEMCACHE_SERVER_NAME -o custom-columns='INTERNAL_IP:.status.addresses[?(@.type=="InternalIP")].address' | head -2 | tail -1`
logEcho "# ADDR: $MEMCACHE_IPADDR"
logEcho "#############################################"

logEcho "#############################################"
logEcho "# RETRIEVING NODE NAMES"
CLIENT_AGENT_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent`
CLIENT_MEASURE_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-measure`
logEcho "# AGENT: $CLIENT_AGENT_NAME"
logEcho "# MEASURE: $CLIENT_MEASURE_NAME"
logEcho "#############################################"

logEcho "#############################################"
logEcho "# STARTING MCPERF ON $CLIENT_AGENT_NAME" AND WAITING 15 SECONDS
logEcho "#############################################"
screen -d -m -S "AGENT_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- './memcache-perf-dynamic/mcperf -T 16 -A' &

sleep 15

logEcho "#############################################"
logEcho "# RUNNING QUERIES"
logEcho "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "./memcache-perf-dynamic/mcperf -s $MEMCACHE_IPADDR --loadonly"

AGENT_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent | awk -v OFS='\t\t' '{print $6}'`

screen -d -m -S "LOAD_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- \
"./memcache-perf-dynamic/mcperf -s $MEMCACHE_IPADDR -a $AGENT_INTERNAL_IP_ADDR \
--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 10 \
--qps_interval 2 --qps_min 5000 --qps_max 100000 > ./mcperf_${CURRENTEPOCTIME}.txt" &

logEcho "#############################################"
logEcho "# STARTING SCHEDULER"
logEcho "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "poetry run python3 ./resource_scheduler/scheduler/main.py"

logEcho "#############################################"
logEcho "# KILL DETACHED MCPERF"
logEcho "#############################################"
DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- "sudo kill $DETACHED_PROC"

DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "sudo kill $DETACHED_PROC"

logEcho "#############################################"
logEcho "# CURRENT RUNNING DETTACHED"
logEcho "#############################################"
screen -ls

logEcho "#############################################"
logEcho "# GETTING MCPERF DATA FROM SERVER"
logEcho "#############################################"
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME:/home/ubuntu/mcperf_${CURRENTEPOCTIME}.txt" ../part4_2_raw_outputs/mcperf_${CURRENTEPOCTIME}.txt --zone europe-west3-a

logEcho "#############################################"
logEcho "# GETTING SCHEDULER LOG FROM SERVER"
logEcho "#############################################"
LOG_FILENAME=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- 'ls ./resource_scheduler/scheduler/log* | xargs -n 1 basename')
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME:/home/ubuntu/resource_scheduler/scheduler/${LOG_FILENAME}" ../part4_2_raw_outputs/${LOG_FILENAME} --zone europe-west3-a