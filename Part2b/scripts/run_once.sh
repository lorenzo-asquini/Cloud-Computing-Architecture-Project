#!/bin/bash

ALL_THREADS_AMOUNT=("1" "2" "4" "8")

ALL_WORKLOADS=("blackscholes" "canneal" "dedup" "ferret" "freqmine" "radix" "vips")

# Create folder for the outputs
mkdir part2b_raw_outputs

for nr_threads in "${ALL_THREADS_AMOUNT[@]}"; do

    for workload in "${ALL_WORKLOADS[@]}"; do

        # Change the number of cores
        sed -i "s/native -n [0-9]\+/native -n $nr_threads/g" parsec-benchmarks/part2b/parsec-$workload.yaml

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
                kubectl create -f parsec-benchmarks/part2b/parsec-$workload.yaml
                echo "Sleeping 15 seconds"
                sleep 15
            fi
            CURRENT_STATUS=$(kubectl get jobs | grep parsec-$workload | awk -v OFS='\t\t' '{print $2}')
        done
        echo "Parsec workload done. Saving output."

        kubectl logs $(kubectl get pods --selector=job-name=parsec-$workload --output=jsonpath='{.items[*].metadata.name}') > part2b_raw_outputs/${workload}_${nr_threads}.txt

        echo "#############################################"
        echo "# DELETING JOB FOR: $workload", WITH THREADS: $nr_threads
        echo "#############################################"

        kubectl delete jobs --all

    done
done