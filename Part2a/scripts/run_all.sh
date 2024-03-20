#!/bin/bash

ALL_INTERFERENCE_TYPES=("none" "cpu" "l1d" "l1i" "l2" "llc" "membw")

ALL_WORKLOADS=("blackscholes" "canneal" "dedup" "ferret" "freqmine" "radix" "vips")

# Create folder for the outputs
mkdir part2a_raw_outputs

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
                echo "Interference pod does not exist, creating."
                kubectl create -f interference/ibench-$interference.yaml
                echo "Sleeping 5 seconds"
                sleep 5
            fi
            CURRENT_STATUS=$(kubectl get pod ibench-$interference | grep ibench-$INTERFEREinterferenceNCE_TYPE | awk -v OFS='\t\t' '{print $2}')
        done
        echo "Intereference pod ibench-$interference is ready for testing."
    fi

    for workload in "${ALL_WORKLOADS[@]}"; do

        echo "#############################################"
        echo "# RUNNING WORKLOAD: $workload"
        echo "#############################################"
        CURRENT_STATUS=$(kubectl get jobs | grep parsec-$workload | awk -v OFS='\t\t' '{print $2}')
        while [[ "$CURRENT_STATUS" != "1/1" ]] # This means the job is done
        do
            if [[ "$CURRENT_STATUS" == "0/1" ]]
            then
                echo "Job not finished yet, sleeping 15 seconds."
                sleep 15
                
            else
                echo "Parsec workload does not exist, creating"
                kubectl create -f parsec-benchmarks/part2a/parsec-$workload.yaml
                echo "Sleeping 15 seconds"
                sleep 15
            fi
            CURRENT_STATUS=$(kubectl get jobs | grep parsec-$workload | awk -v OFS='\t\t' '{print $2}')
        done
        echo "Parsec workload done. Saving output."

        kubectl logs $(kubectl get pods --selector=job-name=parsec-$workload --output=jsonpath='{.items[*].metadata.name}') > part2a_raw_outputs/${workload}_${interference}.txt

        echo "#############################################"
        echo "# DELETING JOB FOR: $workload", WITH INTERFERENCE: $interference
        echo "#############################################"

        kubectl delete jobs --all

    done

    if [[ "$interference" != "none" ]]
    then
        echo "Deleting interference pod"
        kubectl delete pods --all
    fi
done