# How to use the scripts

Assuming that the folder `cloud-comp-arch-project` was already cloned from github.

## Start the cluster

Move the file `setup.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the values of the variables `KOPS_STATE_STORE` and `CCA_PROJECT_PUB_KEY` according to your configuration. The script will end if they are not set.

Run the script with `./setup.sh`. If there is a permission denied error, run `chmod 744 setup.sh` in order to set the permission to execute the script.

Pay attention to possible errors. In particular, it is particularly possible that there may be some errors in setting up the SSH key. If so, run the command manually after the cluster is up (change the file name):
```
kops create secret --name part2a.k8s.local sshpublickey admin -i ~/.ssh/file.pub
```

Even if at the end it says that the parsec server was not labeled, it should still be ok.

## Run the tests on all interferences for multiple times

Move the file `run_all.sh` in the folder `cloud-comp-arch-project`.

Run the script with `./run_all.sh`. If there is a permission denied error, run `chmod 744 run_all.sh` in order to set the permission to execute the script.

It will run the tests for each parsec workload specified in the array `ALL_WORKLOADS`, for all the interferences specified in the array `ALL_INTERFERENCE_TYPES`, one time. For each test, it will save the output in the folder `part2a_raw_outputs`.