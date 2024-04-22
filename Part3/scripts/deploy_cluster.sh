#!/bin/bash

DEFAULT_KOPS_STATE_STORE="gs://cca-eth-2024-group-XXX-ethzid/"
DEFAULT_CCA_PROJECT_PUB_KEY="~/.ssh/file.pub"

# Change these variables according to your configuration
KOPS_STATE_STORE="gs://cca-eth-2024-group-XXX-ethzid/"
CCA_PROJECT_PUB_KEY="~/.ssh/file.pub"

# Exit if the variables are still the default ones
if [ "$KOPS_STATE_STORE" == "$DEFAULT_KOPS_STATE_STORE" ]; then
    echo "KOPS STATE STORE value is still the placeholder one. Change it!"
    exit 1
fi

if [ "$CCA_PROJECT_PUB_KEY" == "$DEFAULT_CCA_PROJECT_PUB_KEY" ]; then
    echo "SSH PUB KEY value is still the placeholder one. Change it!"
    exit 1
fi

echo "Using KOPS STATE STORE: $KOPS_STATE_STORE"
echo "Using path to ssh pub key: $CCA_PROJECT_PUB_KEY"

# Assuming that the bucket was already created

PROJECT=`gcloud config get-value project`

kops create -f ../part3_yaml_files/part3_cheap.yaml

# This may give an error. If so, run it independently
kops create secret --name part3.k8s.local sshpublickey admin -i $CCA_PROJECT_PUB_KEY

kops update cluster --name part3.k8s.local --yes --admin

kops validate cluster --wait 10m

kubectl get nodes -o wide