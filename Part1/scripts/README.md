# How to use the scripts

Assuming that the folder `cloud-comp-arch-project` was already cloned from [github](https://github.com/eth-easl/cloud-comp-arch-project/tree/master).

If at any point you get the error `-bash: ./file.sh: /bin/bash^M: bad interpreter: No such file or directory`, it is caused by some incompatibilities between newlines in Windows and Linux. In order to easily solve the problem, run the command `sed -i -e 's/\r$//' file.sh`.

## Start the cluster

Move the file `deploy_cluster.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the values of the variables `KOPS_STATE_STORE` and `CCA_PROJECT_PUB_KEY` according to your configuration. The script will exit if they are not set.

Run the script with `./deploy_cluster.sh`. If there is a permission denied error, run `chmod 744 deploy_cluster.sh` in order to set the permission to execute the script.

Pay attention to possible errors. In particular, it is particularly possible that there may be some errors in setting up the SSH key. If so, run the command manually after the cluster is up (change the file name):

```
kops create secret --name part1.k8s.local sshpublickey admin -i ~/.ssh/file.pub
```

## Deploy memcached

Move the file `setup_agent_measure.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the value of the variable `CCA_PROJECT_PUB_KEY` according to your configuration. The script will exit if it is not set or if the filename ends with `.pub`.

Run the script with `./setup_agent_measure.sh`. If there is a permission denied error, run `chmod 744 setup_agent_measure.sh` in order to set the permission to execute the script.

This script will upload and run the script `remote_setup.sh` (which must be on the same folder) on the servers. It will ask multiple times for the SSH password if you have set a password for the SSH key. It may be possible that the same error relative to the incompatibilities between newlines in Windows and Linux may appear, so pay attention to the console output.

## Run the tests on all interferences for multiple times

Move the file `run_all.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the value of the variable `CCA_PROJECT_PUB_KEY` according to your configuration. The script will exit if it is not set or if the filename ends with `.pub`.

Run the script with `./run_all.sh`. If there is a permission denied error, run `chmod 744 run_all.sh` in order to set the permission to execute the script.

It will run the tests for all the interferences specified in the array `ALL_INTERFERENCE_TYPES` as many times as it is specified in `RUN_TIMES`. For each test, it will save the output in the folder `part1_raw_outputs`. It will ask multiple times for the SSH password if you have set a password for the SSH key.