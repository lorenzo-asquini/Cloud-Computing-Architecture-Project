#!/bin/bash
MCPERF_TIMEOUT=$1

logEcho() {
    echo $(date -u) "||| $1"
}

if [[ -z "$MCPERF_TIMEOUT" ]]; then
    logEcho "Must specify MCPERF load timeout as argument in seconds (e.g. 1200 for 20 minutes)"
    logEcho "Exiting"
    exit
fi 

# Create folder for the outputs
mkdir ../part4_2_raw_outputs

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
logEcho "# ASSIGNING 2 CORES TO MEMCACHE"
logEcho "#############################################"
MEMCACHED_PID=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "cat /var/run/memcached/memcached.pid" | tr -d '\r')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "sudo taskset -a -cp "0-1" $MEMCACHED_PID"

logEcho "#############################################"
logEcho "# RUNNING QUERIES"
logEcho "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "./memcache-perf-dynamic/mcperf -s $MEMCACHE_IPADDR --loadonly"

AGENT_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent | awk -v OFS='\t\t' '{print $6}'`

screen -d -m -S "LOAD_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- \
"./memcache-perf-dynamic/mcperf -s $MEMCACHE_IPADDR -a $AGENT_INTERNAL_IP_ADDR \
--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t $MCPERF_TIMEOUT \
--qps_interval 10 --qps_min 5000 --qps_max 100000 > ./mcperf_${CURRENTEPOCTIME}.txt" &

logEcho "#############################################"
logEcho "# REMOVING ALL OLD CONTAINERS (IF ANY)"
logEcho "#############################################"
for name in "BLACKSCHOLES" "FERRET" "FREQMINE" "RADIX" "VIPS" "CANNEAL" "DEDUP"; do
    gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "sudo docker remove $name"
done

logEcho "#############################################"
logEcho "# STARTING SCHEDULER"
logEcho "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME" --zone europe-west3-a  -- "sudo python3 ./scheduler/main.py"

logEcho "#############################################"
logEcho "# WAIT FOR MCPERF TO END"
logEcho "#############################################"
while true
do
    PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf' |  grep perf-dynamic)
    if [[ -z "$PROC" ]]; then
        logEcho "MCPERF load finished"
        break
    else
        logEcho "MCPERF load not yet finished, sleeping 10 seconds"
        sleep 10
    fi 
done

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
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$MEMCACHE_SERVER_NAME:/home/ubuntu/log*" ../part4_2_raw_outputs/ --zone europe-west3-a