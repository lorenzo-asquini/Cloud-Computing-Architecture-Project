## YAML files

The YAML files used to execute the tests for Part 4.1 are contained in the folder `part4_3-4_yaml_files`. There are two versions of the file used to create the cluster. `part4.yaml` is the official file and the one that needs to be used for the submission. `part4_cheap.yaml` is a copy of `part4.yaml` where all the machines used in the cluster are cheap. Considering that the various machines required are quite expensive, it does not make sense to waste credits while testing the automatic scripts. Both files require modifying some values according to the configuration.

## Scheduler

### Memcache behavior

Memcache starts with 2 cores and 2 threads. If the CPU usage of memcache is less than 20%, memcache is assigned 1 core. If it's higher than 20%, memcache is assigned 2 cores. Every time a job needs to be started, memcache is assigned 2 cores. Just before exiting, memcached is assigned 2 cores.

### Job assignment

| Workload     | Threads | Cores Id | Dependencies                                   |
| ------------ | ------- | -------- |----------------------------------------------- |
| Memcached    | 2       | 0 or 0,1 | None                                           |
| Radix        | 1       | 1        | None                                           |
! Blackscholes | 2       | 2, 3     | None                                           |
| Ferret       | 2       | 2, 3     | Blackscholes                                   |
| Freqmine     | 2       | 2, 3     | Blackscholes, Ferret                           |
| Canneal      | 2       | 2, 3     | Blackscholes, Ferret, Freqmine                 |
| Dedup        | 2       | 2, 3     | Blackscholes, Ferret, Freqmine, Canneal        |        
| Vips         | 2       | 2, 3     | Blackscholes, Ferret, Freqmine, Canneal, Dedup |

### CPU Quota

A new job is able to start if all the job dependencies have been completed and if the CPU usage of memcache is below 75%. Once a job starts, it is assigned a CPU quota lower than the maximum available for that job. \
For all the jobs that don't share any CPU cores with memcached, the starting CPU quota is half of the maximum and slowly reaches the maximum available in order to not stress too much on the shared resources and cause SLO violations. \
For all the jobs that share CPU cores with memcached, the CPU quota is dynamically assigned during execution. If the CPU usage of memcached is lower than 10%, the maximum quota is assigned. If it's between 10% and 50%, the assigned CPU quota is an interpolation between the minimum and the maximum. If the CPU usage of memcached is above 50%, the job is stopped and resumed only once it is again lower than 50%.

## Analyse data

In `part4_3-4_extracted_data` there is a Python script called `create_plots.py` that will plot the P95 latency, the QPS and the scheduling of the jobs over time. The Python script called `get_job_times.py` will calculate the average execution time and the standard deviation of the different workloads.