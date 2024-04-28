#!/bin/bash

logEcho() {
    echo $(date -u) "||| $1"
}

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

CURRENTEPOCTIME=$(date +%s)
logEcho "Current EPOCH is $CURRENTEPOCTIME"

# Create folder for the outputs
mkdir ../part3_raw_outputs

# Allows running a program remotely infinitely without keeping the connection open
mkdir ~/.screen && chmod 700 ~/.screen
export SCREENDIR=$HOME/.screen

logEcho "#############################################"
logEcho "# RETRIEVING POD IP ADDR"
MEMCACHED_POD_IPADDR=`kubectl get pod some-memcached -o custom-columns=IP:status.podIP | head -2 | tail -1`
logEcho "# ADDR: $MEMCACHED_POD_IPADDR"
logEcho "#############################################"

logEcho "#############################################"
logEcho "# RETRIEVING NODE NAMES"
CLIENT_AGENT_A_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent-a`
CLIENT_AGENT_B_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-agent-b`
CLIENT_MEASURE_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep client-measure`
logEcho "# AGENT: $CLIENT_AGENT_A_NAME"
logEcho "# AGENT: $CLIENT_AGENT_B_NAME"
logEcho "# MEASURE: $CLIENT_MEASURE_NAME"
logEcho "#############################################"

logEcho "#############################################"
logEcho "# STARTING MCPERF ON $CLIENT_AGENT_A_NAME"
logEcho "#############################################"
screen -d -m -S "AGENT_A_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_A_NAME" --zone europe-west3-a  -- './memcache-perf-dynamic/mcperf -T 2 -A' &

logEcho "#############################################"
logEcho "# STARTING MCPERF ON $CLIENT_AGENT_B_NAME"
logEcho "#############################################"
screen -d -m -S "AGENT_B_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_B_NAME" --zone europe-west3-a  -- './memcache-perf-dynamic/mcperf -T 4 -A' &

sleep 15

logEcho "#############################################"
logEcho "# LOAD MEMCACHE DB AND THEN WAITING 15 SECONDS"
logEcho "#############################################"
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- "./memcache-perf-dynamic/mcperf -s $MEMCACHED_POD_IPADDR --loadonly"

sleep 15

logEcho "#############################################"
logEcho "# RUNNING QUERIES AND THEN WAITING 15 SECONDS"
logEcho "#############################################"
AGENT_A_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent-a | awk -v OFS='\t\t' '{print $6}'`
AGENT_B_INTERNAL_IP_ADDR=`kubectl get nodes -o wide | grep client-agent-b | awk -v OFS='\t\t' '{print $6}'`

screen -d -m -S "LOAD_MCPERF" gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME" --zone europe-west3-a  -- \
"./memcache-perf-dynamic/mcperf -s $MEMCACHED_POD_IPADDR -a $AGENT_A_INTERNAL_IP_ADDR -a $AGENT_B_INTERNAL_IP_ADDR \
--noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 10 \
--scan 30000:30500:5 > ./mcperf_${CURRENTEPOCTIME}.txt" &

sleep 15

logEcho "#############################################"
logEcho "# SETTING UP STATE TRACKING"
logEcho "#############################################"
# Declare job types and states
declare -a jobtypes=(blackscholes canneal dedup radix ferret freqmine vips)
declare -a jobstates=(started finished error)

logEcho "#############################################"
logEcho "# DECLARING DEPENDENCIES"
logEcho "#############################################"
# Declare job inter dependencies
declare -a blackscholes_dependencies=()
declare -a canneal_dependencies=()
declare -a dedup_dependencies=()
declare -a radix_dependencies=()
declare -a ferret_dependencies=(canneal dedup)
declare -a freqmine_dependencies=(radix)
declare -a vips_dependencies=(radix freqmine)

stateGet() { 
    local job=$1 state=$2
    local i="jobtypes_${job}_${state}"
    echo "${!i}"
}

finishedWithNoErrors() {
    local job=$1
    local jobFinishedState=$(stateGet $job finished)
    local jobErrorState=$(stateGet $job error)
    if [ $jobFinishedState == true ] && [ $jobErrorState == false ]
    then
        echo true
    else
        echo false
    fi
}

canStartJob() {
    local job=$1
    local deps_addr="${job}_dependencies"
    local deps_array="${deps_addr}[@]"

    if [ $(stateGet $job started) == false ]
    then
        local canStart=true
        for job_dep in "${!deps_array}"
        do
            if [ $(finishedWithNoErrors $job_dep) == false ]
            then
                canStart=false
                break
            fi
        done
        echo $canStart
    else
        echo false
    fi
}

# Set everything to false at first
for jobtype in "${jobtypes[@]}"
do
    for jobstate in "${jobstates[@]}"
    do
        declare "jobtypes_${jobtype}_${jobstate}=false"
    done
done

logEcho "#############################################"
logEcho "# STARTING JOBS"
logEcho "#############################################"

# Start initial jobs
for jobtype in "${jobstostartfirst[@]}"
do
    kubectl create -f "../part3_yaml_files/benchmarks/parsec-${jobtype}.yaml"
    declare "jobtypes_${jobtype}_started=true"
done

while true
do

    PODS_STATUS=$(kubectl get pod)
    JOBS_STATUS=$(kubectl get jobs)
    
    for jobtype in "${jobtypes[@]}"
    do
        if [ $(canStartJob $jobtype) == true ]
        then
            logEcho "Starting $jobtype!"
            kubectl create -f "../part3_yaml_files/benchmarks/parsec-$jobtype.yaml"
            declare "jobtypes_${jobtype}_started=true"
        fi

        COMPLETE=$(echo "$JOBS_STATUS" | grep "parsec-$jobtype" | awk -v OFS='\t\t' '{print $2}')
        FINISHED=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)
        declare "jobtypes_${jobtype}_finished=${FINISHED}"

        STATUS=$(echo "$PODS_STATUS" | grep parsec-blackscholes | awk -v OFS='\t\t' '{print $3}')
        ERROR=$([ "$STATUS" == "Error" ] && echo true || echo false)
        declare "jobtypes_${jobtype}_error=${ERROR}"
    done

    breakLoop=false
    # Check if no errors
    for jobtype in "${jobtypes[@]}"
    do
        if [ $(stateGet $jobtype error) == true ]
        then
           logEcho "Job $jobtype has errors."
           logEcho ERROR! ERROR! ERROR!
           logEcho $PODS_STATUS
           logEcho ERROR! ERROR! ERROR!

           breakLoop=true
           break
        fi
    done

    if [ $breakLoop == true ]
    then
        break
    fi

    # Check if all done
    breakLoop=true
    for jobtype in "${jobtypes[@]}"
    do
        if [ $(stateGet $jobtype finished) == false ]
        then
           logEcho "$jobtype is not yet finished"
           breakLoop=false
           break
        fi
    done

    if [ $breakLoop == true ]
    then
        logEcho "All jobs succesfully completed."
        break
    fi
    
    logEcho "Sleeping 5 seconds"
    sleep 5
done

kubectl get pods -o json > results_${CURRENTEPOCTIME}.json

logEcho "#############################################"
logEcho "# KILLING ALL JOBS"
logEcho "#############################################"
kubectl delete jobs --all

logEcho "#############################################"
logEcho "# KILL DETACHED MCPERF"
logEcho "#############################################"
DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_A_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_A_NAME" --zone europe-west3-a  -- "kill $DETACHED_PROC"

DETACHED_PROC=$(gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_B_NAME" --zone europe-west3-a  -- 'ps -aux | grep mcperf | head -1' | awk '{print $2}')
gcloud compute ssh --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_B_NAME" --zone europe-west3-a  -- "kill $DETACHED_PROC"

logEcho "#############################################"
logEcho "# CURRENT RUNNING DETTACHED"
logEcho "#############################################"
screen -ls

logEcho "#############################################"
logEcho "# GETTING MCPERF DATA"
logEcho "#############################################"
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_MEASURE_NAME:/home/ubuntu/mcperf_${CURRENTEPOCTIME}.txt" ../part3_raw_outputs/mcperf_${CURRENTEPOCTIME}.txt --zone europe-west3-a
