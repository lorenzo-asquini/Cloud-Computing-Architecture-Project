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

RUN_TIMES=3

# Create folder for the outputs
mkdir part4_1_raw_outputs

# Allows running a program remotely infinitely without keeping the connection open
mkdir ~/.screen && chmod 700 ~/.screen
export SCREENDIR=$HOME/.screen

MEMCACHE_SERVER_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep memcache-server`
echo "#############################################"
echo "# RETRIEVING MEMCACHE IP ADDR"
MEMCACHE_IPADDR=`kubectl get nodes $MEMCACHE_SERVER_NAME -o custom-columns='INTERNAL_IP:.status.addresses[?(@.type=="InternalIP")].address' | head -2 | tail -1`
echo "# ADDR: $MEMCACHE_IPADDR"
echo "#############################################"

echo "#############################################"
echo "# RETRIEVING NODE NAMES"
CLIENT_AGENT_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent`
CLIENT_MEASURE_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-measure`
echo "# AGENT: $CLIENT_AGENT_NAME"
echo "# MEASURE: $CLIENT_MEASURE_NAME"
echo "#############################################"

echo "#############################################"
echo "# STARTING MCPERF ON $CLIENT_AGENT_NAME" AND WAITING 15 SECONDS
echo "#############################################"
screen -d -m -S "AGENT_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- './memcache-perf/mcperf -T 16 -A' &

sleep 15

echo "#############################################"
echo "# LOAD MEMCACHE DB"
echo "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "./memcache-perf-dynamic/mcperf -s $MEMCACHE_IPADDR --loadonly"

for threads in 1 2; do
    for cores in "0" "0-1"; do

        # Removed most of the configuration comments to lower the number of lines
        memcache_configuration="
-d
logfile /var/log/memcached.log
-m 1024
-p 11211
-u memcache
-l $MEMCACHE_IPADDR
-P /var/run/memcached/memcached.pid
-t $threads
"
        # Set the new configuration
        echo "#############################################"
        echo "# SET THE NEW MEMCACHE CONFIGURATION WITH $threads THREADS AND $cores CORES"
        echo "#############################################"
        gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "echo "$memcache_configuration" | sudo tee /etc/memcached.conf"
        gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "sudo systemctl restart memcached"
        gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "sudo taskset -a -cp $cores $(cat /var/run/memcached/memcached.pid)"

        for ((iteration=0; iteration<RUN_TIMES; iteration++)); do

            echo "#############################################"
            echo "# RUNNING QUERIES"
            echo "#############################################"
            AGENT_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent | awk -v OFS='\t\t' '{print $6}'`
            gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- \
            "./memcache-perf-dynamic/mcperf -s $MEMCACHE_IPADDR -a $AGENT_INTERNAL_IP_ADDR \
            --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 \
            --scan 5000:125000:5000" > part4_1_raw_outputs/threads=${threads}_cores=${cores}_${iteration}.txt
        done
    done
done

echo "#############################################"
echo "# KILL DETACHED MCPERF"
echo "#############################################"
DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- "kill $DETACHED_PROC"

echo "#############################################"
echo "# CURRENT RUNNING DETTACHED"
echo "#############################################"
screen -ls