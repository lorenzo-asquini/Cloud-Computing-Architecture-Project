#!/bin/bash


if [[ "$CCA_PROJECT_PUB_KEY" == *.pub ]]; then
    echo "Path to the SSH key ends with .pub. In this case, remove it!"
    exit 1
fi

if [ "$CCA_PROJECT_PUB_KEY" == "$DEFAULT_CCA_PROJECT_PUB_KEY" ]; then
    echo "SSH PUB KEY value is still the placeholder one. Change it!"
    exit 1
fi

CURRENTEPOCTIME=$(date +%s)
echo "Current EPOCH is $CURRENTEPOCTIME"

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
--scan 30000:30500:5 > ./mcperf_${CURRENTEPOCTIME}.txt" &

sleep 15

echo "#############################################"
echo "# SETTING UP STATE TRACKING"
echo "#############################################"
# Declare job types and states
declare -a jobtypes=(blackscholes canneal dedup radix ferret freqmine vips)
declare -a jobstates=(started finished error)
declare -a jobstostartfirst=(blackscholes canneal dedup radix)

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

# Set everything to false at first
for jobtype in "${jobtypes[@]}"
do
    for jobstate in "${jobstates[@]}"
    do
        declare "jobtypes_${jobtype}_${jobstate}=false"
    done
done

echo "#############################################"
echo "# STARTING JOBS"
echo "#############################################"

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
        COMPLETE=$(echo "$JOBS_STATUS" | grep "parsec-$jobtype" | awk -v OFS='\t\t' '{print $2}')
        FINISHED=$([ "$COMPLETE" == "1/1" ] && echo true || echo false)
        declare "jobtypes_${jobtype}_finished=${FINISHED}"

        STATUS=$(echo "$PODS_STATUS" | grep parsec-blackscholes | awk -v OFS='\t\t' '{print $3}')
        ERROR=$([ "$STATUS" == "Error" ] && echo true || echo false)
        declare "jobtypes_${jobtype}_error=${ERROR}"
    done

    # Ferret
    # Start Ferret if Canneal and Dedup have finished succesfully, and if it was not already started
    if [ $(finishedWithNoErrors canneal) == true ] && \
       [ $(finishedWithNoErrors dedup) == true ] && \
       [ $(stateGet ferret started) == false ] 
    then
        echo Starting Ferret!
        kubectl create -f ../part3_yaml_files/benchmarks/parsec-ferret.yaml
        declare "jobtypes_ferret_started=true"
    fi

    # Freqmine
    # Start Freqmine if Radix has finished succesfully, and if it was not already started
    if [ $(finishedWithNoErrors radix) == true ] && \
       [ $(stateGet freqmine started) == false ] 
    then
        echo Starting Freqmine!
        kubectl create -f ../part3_yaml_files/benchmarks/parsec-freqmine.yaml
        declare "jobtypes_freqmine_started=true"
    fi

    # Vips
    # Start Vips if Radix and Freqmine has finished succesfully, and if it was not already started
    if [ $(finishedWithNoErrors radix) == true ] && \
       [ $(finishedWithNoErrors freqmine) == true ] && \
       [ $(stateGet vips started) == false ] 
    then
        echo Starting Vips!
        kubectl create -f ../part3_yaml_files/benchmarks/parsec-vips.yaml
        declare "jobtypes_vips_started=true"
    fi

    breakLoop=false
    # Check if no errors
    for jobtype in "${jobtypes[@]}"
    do
        if [ $(stateGet $jobtype error) == true ]
        then
           echo ERROR! ERROR! ERROR!
           echo $PODS_STATUS
           echo ERROR! ERROR! ERROR!

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
           echo "$jobtype is not yet finished"
           breakLoop=false
        fi
    done

    if [ $breakLoop == true ]
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

echo "#############################################"
echo "# GETTING MCPERF DATA"
echo "#############################################"
gcloud compute scp --ssh-key-file $CCA_PROJECT_PUB_KEY "ubuntu@$CLIENT_AGENT_NAME:/home/ubuntu/mcperf_${CURRENTEPOCTIME}.txt" ../part3_raw_outputs/mcperf_${CURRENTEPOCTIME}.txt --zone europe-west3-a