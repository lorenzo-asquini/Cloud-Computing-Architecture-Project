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

CURRENTEPOCTIME=$(date +%s)

# Create folder for the outputs
mkdir ../part3_raw_outputs

# Allows running a program remotely infinitely without keeping the connection open
mkdir ~/.screen && chmod 700 ~/.screen
export SCREENDIR=$HOME/.screen

echo "#############################################"
echo "# RETRIEVING POD IP ADDR"
MEMCACHED_POD_IPADDR=`kubectl get pod some-memcached -o custom-columns=IP:status.podIP | head -2 | tail -1`
echo "# ADDR: $MEMCACHED_POD_IPADDR"
echo "#############################################"

echo "#############################################"
echo "# RETRIEVING NODE NAMES"
CLIENT_AGENT_A_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent-a`
CLIENT_AGENT_B_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent-b`
CLIENT_MEASURE_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-measure`
echo "# AGENT: $CLIENT_AGENT_A_NAME"
echo "# AGENT: $CLIENT_AGENT_B_NAME"
echo "# MEASURE: $CLIENT_MEASURE_NAME"
echo "#############################################"

echo "#############################################"
echo "# STARTING MCPERF ON $CLIENT_AGENT_A_NAME"
echo "#############################################"
screen -d -m -S "AGENT_A_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_A_NAME" --zone europe-west3-a  -- './memcache-perf-dynamic/mcperf -T 2 -A' &

echo "#############################################"
echo "# STARTING MCPERF ON $CLIENT_AGENT_B_NAME"
echo "#############################################"
screen -d -m -S "AGENT_B_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_B_NAME" --zone europe-west3-a  -- './memcache-perf-dynamic/mcperf -T 4 -A' &

sleep 15

echo "#############################################"
echo "# LOAD MEMCACHE DB AND THEN WAITING 15 SECONDS"
echo "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "./memcache-perf-dynamic/mcperf -s $MEMCACHED_POD_IPADDR --loadonly"

sleep 15

echo "#############################################"
echo "# RUNNING QUERIES AND THEN WAITING 15 SECONDS"
echo "#############################################"
AGENT_A_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent-a | awk -v OFS='\t\t' '{print $6}'`
AGENT_B_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent-b | awk -v OFS='\t\t' '{print $6}'`

screen -d -m -S "LOAD_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- \
"./memcache-perf-dynamic/mcperf -s $MEMCACHED_POD_IPADDR -a $AGENT_A_INTERNAL_IP_ADDR -a $AGENT_B_INTERNAL_IP_ADDR \
--noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 10 \
--scan 30000:30500:5" > ../part3_raw_outputs/mcperf_${CURRENTEPOCTIME}.txt

sleep 15

echo "#############################################"
echo "# STARTING JOBS"
echo "#############################################"

# Start jobs at first
kubectl create -f ../part3_yaml_files/benchmarks/parsec-blackscholes.yaml
kubectl create -f ../part3_yaml_files/benchmarks/parsec-canneal.yaml
kubectl create -f ../part3_yaml_files/benchmarks/parsec-dedup.yaml
kubectl create -f ../part3_yaml_files/benchmarks/parsec-radix.yaml

# Handle status. Each benchmark has: (started, finished, error)
declare -A benchmarks

benchmarks["blackscholes","started"]=true
benchmarks["blackscholes","finished"]=false
benchmarks["blackscholes","error"]=false

benchmarks["canneal","started"]=true
benchmarks["canneal","finished"]=false
benchmarks["canneal","error"]=false

benchmarks["dedup","started"]=true
benchmarks["dedup","finished"]=false
benchmarks["dedup","error"]=false

benchmarks["radix","started"]=true
benchmarks["radix","finished"]=false
benchmarks["radix","error"]=false

benchmarks["ferret","started"]=false
benchmarks["ferret","finished"]=false
benchmarks["ferret","error"]=false

benchmarks["freqmine","started"]=false
benchmarks["freqmine","finished"]=false
benchmarks["freqmine","error"]=false

benchmarks["vips","started"]=false
benchmarks["vips","finished"]=false
benchmarks["vips","error"]=false

while true
do

    PODS_STATUS=$(kubectl get pod)
    JOBS_STATUS=$(kubectl get jobs)
    
    # Blackscholes
    COMPLETE=$(echo "$JOBS_STATUS" | grep parsec-blackscholes | awk -v OFS='\t\t' '{print $2}')
    benchmarks["blackscholes","finished"]=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)  # Finish
    STATUS=$(echo "$PODS_STATUS" | grep parsec-blackscholes | awk -v OFS='\t\t' '{print $3}')
    benchmarks["blackscholes","error"]=$([ "$STATUS" == "Error" ] && echo true || echo false) # Error

    # Canneal
    COMPLETE=$(echo "$JOBS_STATUS" | grep parsec-canneal | awk -v OFS='\t\t' '{print $2}')
    benchmarks["canneal","finished"]=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)  # Finish
    STATUS=$(echo "$PODS_STATUS" | grep parsec-canneal | awk -v OFS='\t\t' '{print $3}')
    benchmarks["canneal","error"]=$([ "$STATUS" == "Error" ] && echo true || echo false) # Error

    # Dedup
    COMPLETE=$(echo "$JOBS_STATUS" | grep parsec-dedup | awk -v OFS='\t\t' '{print $2}')
    benchmarks["dedup","finished"]=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)  # Finish
    STATUS=$(echo "$PODS_STATUS" | grep parsec-dedup | awk -v OFS='\t\t' '{print $3}')
    benchmarks["dedup","error"]=$([ "$STATUS" == "Error" ] && echo true || echo false) # Error

    # Radix
    COMPLETE=$(echo "$JOBS_STATUS" | grep parsec-radix | awk -v OFS='\t\t' '{print $2}')
    benchmarks["radix","finished"]=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)  # Finish
    STATUS=$(echo "$PODS_STATUS" | grep parsec-radix | awk -v OFS='\t\t' '{print $3}')
    benchmarks["radix","error"]=$([ "$STATUS" == "Error" ] && echo true || echo false) # Error

    # Ferret

    # Start Ferret if Canneal and Dedup have finished succesfully, and if it was not alCOMPLETE started
    if [ ${benchmarks["canneal","finished"]} == true ] && [ ${benchmarks["canneal","error"]} == false ] && \
       [ ${benchmarks["dedup","finished"]} == true ] && [ ${benchmarks["dedup","error"]} == false ] && \
       [ ${benchmarks["ferret","started"]} == false ] 
    then
        echo Starting Ferret!
        kubectl create -f ../part3_yaml_files/benchmarks/parsec-ferret.yaml
        benchmarks["ferret","started"]=true
    fi

    COMPLETE=$(echo "$JOBS_STATUS" | grep parsec-ferret | awk -v OFS='\t\t' '{print $2}')
    benchmarks["ferret","finished"]=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)  # Finish
    STATUS=$(echo "$PODS_STATUS" | grep parsec-ferret | awk -v OFS='\t\t' '{print $3}')
    benchmarks["ferret","error"]=$([ "$STATUS" == "Error" ] && echo true || echo false) # Error

    # Freqmine

    # Start Freqmine if Radix has finished succesfully, and if it was not alCOMPLETE started
    if [ ${benchmarks["radix","finished"]} == true ] && [ ${benchmarks["radix","error"]} == false ] && \
       [ ${benchmarks["freqmine","started"]} == false ] 
    then
        echo Starting Freqmine!
        kubectl create -f ../part3_yaml_files/benchmarks/parsec-freqmine.yaml
        benchmarks["freqmine","started"]=true
    fi

    COMPLETE=$(echo "$JOBS_STATUS" | grep parsec-freqmine | awk -v OFS='\t\t' '{print $2}')
    benchmarks["freqmine","finished"]=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)  # Finish
    STATUS=$(echo "$PODS_STATUS" | grep parsec-freqmine | awk -v OFS='\t\t' '{print $3}')
    benchmarks["freqmine","error"]=$([ "$STATUS" == "Error" ] && echo true || echo false) # Error

    # Vips

    # Start Vips if Radix and Freqmine has finished succesfully, and if it was not alCOMPLETE started

    if [ ${benchmarks["radix","finished"]} == true ] && [ ${benchmarks["radix","error"]} == false ] && \
       [ ${benchmarks["freqmine","finished"]} == true ] && [ ${benchmarks["freqmine","error"]} == false ] && \
       [ ${benchmarks["vips","started"]} == false ] 
    then
        echo Starting Vips!
        kubectl create -f ../part3_yaml_files/benchmarks/parsec-vips.yaml
        benchmarks["vips","started"]=true
    fi

    COMPLETE=$(echo "$JOBS_STATUS" | grep parsec-vips | awk -v OFS='\t\t' '{print $2}')
    benchmarks["vips","finished"]=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)  # Finish
    STATUS=$(echo "$PODS_STATUS" | grep parsec-vips | awk -v OFS='\t\t' '{print $3}')
    benchmarks["vips","error"]=$([ "$STATUS" == "Error" ] && echo true || echo false) # Error

    # Check if no errors
    if [ ${benchmarks["blackscholes","error"]} == true ] || \
       [ ${benchmarks["canneal","error"]} == true ] || \
       [ ${benchmarks["dedup","error"]} == true ] || \
       [ ${benchmarks["radix","error"]} == true ] || \
       [ ${benchmarks["ferret","error"]} == true ] || \
       [ ${benchmarks["freqmine","error"]} == true ] || \
       [ ${benchmarks["vips","error"]} == true ] 
    then
           echo ERROR! ERROR! ERROR!
           echo $JOBS_STATUS
           echo ERROR! ERROR! ERROR!
           break
    fi

    # Check if all done
    if [ ${benchmarks["blackscholes","finished"]} == true ] && \
       [ ${benchmarks["canneal","finished"]} == true ] && \
       [ ${benchmarks["dedup","finished"]} == true ] && \
       [ ${benchmarks["radix","finished"]} == true ] && \
       [ ${benchmarks["ferret","finished"]} == true ] && \
       [ ${benchmarks["freqmine","finished"]} == true ] && \
       [ ${benchmarks["vips","finished"]} == true ] 
    then
           break
    fi

done

kubectl get pods -o json > results_${CURRENTEPOCTIME}.json

echo "#############################################"
echo "# KILLING ALL JOBS"
echo "#############################################"
kubectl delete jobs --all

echo "#############################################"
echo "# KILL DETACHED MCPERF"
echo "#############################################"
DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_A_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_A_NAME" --zone europe-west3-a  -- "kill $DETACHED_PROC"

DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_B_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_B_NAME" --zone europe-west3-a  -- "kill $DETACHED_PROC"

echo "#############################################"
echo "# CURRENT RUNNING DETTACHED"
echo "#############################################"
screen -ls