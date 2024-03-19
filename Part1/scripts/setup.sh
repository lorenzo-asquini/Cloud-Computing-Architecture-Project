echo "Using KOPS STATE STORE: $KOPS_STATE_STORE"
echo "Using path to ssh pub key: $CCA_PROJECT_PUB_KEY"

gsutil mb $KOPS_STATE_STORE

PROJECT=`gcloud config get-value project`

kops create -f part1.yaml

kops create secret --name part1.k8s.local sshpublickey admin -i $CCA_PROJECT_PUB_KEY

kops update cluster --name part1.k8s.local --yes --admin

kops validate cluster --wait 10m

kubectl get nodes -o wide