# How to use the scripts

Assuming that the folder `cloud-comp-arch-project` was already cloned from github.

## Start the cluster

Move the file `setup.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the values of the variables `KOPS_STATE_STORE` and `CCA_PROJECT_PUB_KEY` according to your configuration. The script will end if they are not set.

Run the script with `./setup.sh`. If there is a permission denied error, run `chmod 744 setup.sh` in order to set the permission to execute the script.

Pay attention to possible errors. In particular, it is particularly possible that there may be some errors in setting up the SSH key. If so, run the command manually after the cluster is up (change the file name):
```
kops create secret --name part1.k8s.local sshpublickey admin -i ~/.ssh/file.pub
```

## Deploy memcached

Move the file `deploy.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the value of the variable `CCA_PROJECT_PUB_KEY` according to your configuration. The script will end if it is not set or if the filename ends with `.pub`.

Run the script with `./deploy.sh`. If there is a permission denied error, run `chmod 744 deploy.sh` in order to set the permission to execute the script.

This script will upload and run the script `run_on_deployed.sh` (which must be on the same folder) on the servers. It will ask multiple times the SSH password.

## Run the tests on all interferences for multiple times

Move the file `run.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the value of the variable `CCA_PROJECT_PUB_KEY` according to your configuration. The script will end if it is not set or if the filename ends with `.pub`.

It will run the tests for all the interferences specified in the array `ALL_INTERFERENCE_TYPES` as many times as it is specified in `RUN_TIMES`. For each test, it will save the output in the folder `outputs`. It will ask for the SSH password multiple times.