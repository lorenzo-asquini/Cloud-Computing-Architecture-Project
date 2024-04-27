# How to use the scripts

Modify the values according to your configuration in `config.sh`.

If you get the error `-bash: ./file.sh: /bin/bash^M: bad interpreter: No such file or directory`, it is caused by some incompatibilities between newlines in Windows and Linux. In order to easily solve the problem, run the command `sed -i -e 's/\r$//' file.sh`.

The script work assuming that they are located in the folder `scripts` and that its parent folder contains the folder `part4_1_yaml_files`.

No need to move files or folders in `cloud-comp-arch-project`.

## Start the cluster

Consider the file `deploy_cluster.sh`. \
Change the deployment between the cheap cluster and the official cluster according to the needs.

Run the script with `./deploy_cluster.sh`. If there is a permission denied error, run `chmod 744 deploy_cluster.sh` in order to set the permission to execute the script.

Pay attention to possible errors. In particular, it is particularly possible that there may be some errors in setting up the SSH key. If so, run the command manually after the cluster is up (change the file name):
```
kops create secret --name part4.k8s.local sshpublickey admin -i ~/.ssh/file.pub
```

## Deploy memcached

Consider the file `setup_agent_measure.sh`.

Run the script with `./setup_agent_measure.sh`. If there is a permission denied error, run `chmod 744 setup_agent_measure.sh` in order to set the permission to execute the script.

This script will upload and run the scripts `remote_setup.sh` and `remote_setup_memcache.sh` (which must be on the same folder) on the servers. It will ask multiple times for the SSH password if you have set a password for the key.

## Run the tests on all interferences for multiple times

Consider the file `run_all.sh`.

Run the script with `./run_all.sh`. If there is a permission denied error, run `chmod 744 run_all.sh` in order to set the permission to execute the script.

It will run the tests for all the configurations given the number of threads and the number of cores. For each configuration, after restarting the memcache service, it will execute the tests for 3 times.