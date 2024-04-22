#!/bin/bash

DEFAULT_KOPS_STATE_STORE="gs://cca-eth-2024-group-XXX-ethzid/"

# Change this variable according to your configuration
KOPS_STATE_STORE="gs://cca-eth-2024-group-XXX-ethzid/"

# Exit if the variable is still the default one
if [ "$KOPS_STATE_STORE" == "$DEFAULT_KOPS_STATE_STORE" ]; then
    echo "KOPS STATE STORE value is still the placeholder one. Change it!"
    exit 1
fi

echo "Using KOPS STATE STORE: $KOPS_STATE_STORE"

# Assuming that the bucket was already created

PROJECT=`gcloud config get-value project`

kops create -f part2b.yaml

kops update cluster --name part2b.k8s.local --yes --admin

kops validate cluster --wait 10m

kubectl get nodes -o wide

PARSEC_NODE_NAME=`kubectl get nodes -o custom-columns=NAME:metadata.name | grep parsec-server`
kubectl label nodes $PARSEC_NODE_NAME cca-project-nodetype=parsec