# How to use the scripts

Assuming that the folder `cloud-comp-arch-project` was already cloned from github.

If you get the error `-bash: ./file.sh: /bin/bash^M: bad interpreter: No such file or directory`, it is caused by some incompatibilities between newlines in Windows and Linux. In order to easily solve the problem, run the command `sed -i -e 's/\r$//' file.sh`.

## Start the cluster

Move the file `deploy_cluster.sh` in the folder `cloud-comp-arch-project`. \
Inside the file, change the value of the variable `KOPS_STATE_STORE` according to your configuration. The script will end if it is not set.

Run the script with `./deploy_cluster.sh`. If there is a permission denied error, run `chmod 744 deploy_cluster.sh` in order to set the permission to execute the script.

Even if at the end it says that the parsec server was not labeled, it should still be ok.

## Run the tests using different number of threads, for all workloads

Move the file `run_all.sh` in the folder `cloud-comp-arch-project`.

Run the script with `./run_all.sh`. If there is a permission denied error, run `chmod 744 run_all.sh` in order to set the permission to execute the script.

It will run the tests for each parsec workload specified in the array `ALL_WORKLOADS`, for all the number of threads specified in the array `ALL_THREADS_AMOUNT`, one time. For each test, it will save the output in the folder `part2a_raw_outputs`.