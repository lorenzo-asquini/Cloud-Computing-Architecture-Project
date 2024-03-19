#!/bin/bash
AVAILABLE_TYPES=("none" "cpu" "l1d" "l1i" "l2" "llc" "membw")
INTERFERENCE_TYPE=$1
KILL_INTERFERENCE_POD_AT_CLEANUP=$2

if [[ ${AVAILABLE_TYPES[@]} =~ $INTERFERENCE_TYPE ]]
then
  echo "Proceeding running tests with interference type: $INTERFERENCE_TYPE"
else
  echo "Interference type not found. Supported types: ${AVAILABLE_TYPES[*]}"
  exit 1
fi

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

echo "#############################################"
echo "# LOAD MEMCACHE DB"
echo "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "./memcache-perf/mcperf -s $POD_IPADDR --loadonly"

echo "#############################################"
echo "# PREPARING OUTPUT"
echo "#############################################"
mkdir outputs
CURRENT_DT=$(date +%Y%m%d)
CURRENT_TS=$(date +%H%M%S)
mkdir -p "outputs/$INTERFERENCE_TYPE/$CURRENT_DT"

if [[ "$INTERFERENCE_TYPE" != "none" ]]
then
    echo "#############################################"
    echo "# PREPARING INTERFERENCE TYPE: $INTERFERENCE_TYPE"
    echo "#############################################"
    CURRENT_STATUS=$(kubectl get pod ibench-$INTERFERENCE_TYPE | grep ibench-$INTERFERENCE_TYPE | awk -v OFS='\t\t' '{print $2}')
    while [[ "$CURRENT_STATUS" != "1/1" ]] # This means it's ready
    do
        if [[ "$CURRENT_STATUS" == "0/1" ]]
        then
            echo "Interference pod not ready, sleeping 15 seconds."
            sleep 15
            
        else
            echo "Interference pod does not exist, creating"
            kubectl create -f interference/ibench-$INTERFERENCE_TYPE.yaml
            echo "Sleeping 15 seconds"
            sleep 15
        fi
        CURRENT_STATUS=$(kubectl get pod ibench-$INTERFERENCE_TYPE | grep ibench-$INTERFERENCE_TYPE | awk -v OFS='\t\t' '{print $2}')
    done
    echo "Intereference pod ibench-$INTERFERENCE_TYPE is ready for testing."
fi

echo "#############################################"
echo "# RUNNING QUERIES"
echo "#############################################"
AGENT_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent | awk -v OFS='\t\t' '{print $6}'`
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- \
"./memcache-perf/mcperf -s $POD_IPADDR -a $AGENT_INTERNAL_IP_ADDR \
--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 \
--scan 5000:55000:5000" > outputs/$INTERFERENCE_TYPE/$CURRENT_DT/$CURRENT_TS

echo "#############################################"
echo "# KILL DETACHED MCPERF"
echo "#############################################"
DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME" --zone europe-west3-a  -- "kill $DETACHED_PROC"

if [[ "$INTERFERENCE_TYPE" != "none" ]]
then
    if [[ $KILL_INTERFERENCE_POD_AT_CLEANUP -eq 1 ]]
    then
        echo "Deleting interference pod"
        kubectl delete pods ibench-$INTERFERENCE_TYPE
    fi
fi

echo "#############################################"
echo "# CURRENT RUNNING DETTACHED"
echo "#############################################"
screen -ls