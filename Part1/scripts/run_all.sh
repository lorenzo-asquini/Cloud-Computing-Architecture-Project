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

ALL_INTERFERENCE_TYPES=("none" "cpu" "l1d" "l1i" "l2" "llc" "membw")

RUN_TIMES=3

# Create folder for the outputs
mkdir part1_raw_outputs

# Allows running a program remotely infinitely without keeping the connection open
mkdir ~/.screen && chmod 700 ~/.screen
export SCREENDIR=$HOME/.screen

echo "#############################################"
echo "# RETRIEVING POD IP ADDR"
POD_IPADDR=`kubectl get pod some-memcached -o custom-columns=IP:status.podIP | head -2 | tail -1`
echo "# ADDR: $POD_IPADDR"
echo "#############################################"

echo "#############################################"
echo "# RETRIEVING NODE NAMES"
CLIENT_AGENT_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent`
CLIENT_MEASURE_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-measure`
echo "# AGENT: $CLIENT_AGENT_NAME"
echo "# MEASURE: $CLIENT_MEASURE_NAME"
echo "#############################################"

echo "#############################################"
echo "# STARTING MCPERF ON $CLIENT_AGENT_NAME"
echo "#############################################"
screen -d -m -S "AGENT_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- './memcache-perf/mcperf -T 16 -A' &

sleep 15

echo "#############################################"
echo "# LOAD MEMCACHE DB"
echo "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "./memcache-perf/mcperf -s $POD_IPADDR --loadonly"

for interference in "${ALL_INTERFERENCE_TYPES[@]}"; do

    # Create interference pod
    if [[ "$interference" != "none" ]]
    then
        echo "#############################################"
        echo "# PREPARING INTERFERENCE TYPE: $interference"
        echo "#############################################"
        CURRENT_STATUS=$(kubectl get pod ibench-$interference | grep ibench-$interference | awk -v OFS='\t\t' '{print $2}')
        while [[ "$CURRENT_STATUS" != "1/1" ]] # This means it's ready
        do
            if [[ "$CURRENT_STATUS" == "0/1" ]]
            then
                echo "Interference pod not ready, sleeping 15 seconds."
                sleep 15
                
            else
                echo "Interference pod does not exist, creating"
                kubectl create -f interference/ibench-$interference.yaml
                echo "Sleeping 15 seconds"
                sleep 15
            fi
            CURRENT_STATUS=$(kubectl get pod ibench-$interference | grep ibench-$INTERFEREinterferenceNCE_TYPE | awk -v OFS='\t\t' '{print $2}')
        done
        echo "Intereference pod ibench-$interference is ready for testing."
    fi

    for ((iteration=0; iteration<RUN_TIMES; iteration++)); do

        echo "#############################################"
        echo "# RUNNING QUERIES"
        echo "#############################################"
        AGENT_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent | awk -v OFS='\t\t' '{print $6}'`
        gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- \
        "./memcache-perf/mcperf -s $POD_IPADDR -a $AGENT_INTERNAL_IP_ADDR \
        --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 \
        --scan 5000:55000:5000" > part1_raw_outputs/${interference}_${iteration}.txt
    done

    if [[ "$interference" != "none" ]]
    then
        echo "Deleting interference pod"
        kubectl delete pods ibench-$interference
    fi
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