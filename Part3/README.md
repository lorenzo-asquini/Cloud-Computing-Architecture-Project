## YAML files

The YAML files used to execute the tests for Part 3 are contained in the folder `part3_yaml_files`. Apart from the files required to run the benchmarks and memcached, there are two versions of the file used to create the cluster. `part3.yaml` is the official file and the one that needs to be used for the submission. `part3_cheap.yaml` is a copy of `part3.yaml` where all the machines used in the cluster are cheap. Considering that the various machines required are quite expensive, it does not make sense to waste credits while testing the automatic scripts. Both files require modifying some values according to the configuration.

Inside each YAML file that contains a `Job` or a `Pod` change the value associated to `spec/nodeSelector/cca-project-nodetype` according to which one should be the node where that job or pod should run. The options are: `node-a-2core`, `node-b-4core` and `node-c-8core`.

For the benchmarks, it's possible to change the number of threads they will use by changing the number that comes after the flag `-n` in the value associated to `spec/template/spec/containers/args` in the respective YAML files.

## Scheduling policy

The dependencies represent which workloads need to terminate their execution in that specific node before the current workload can be started.

**Running on `node-a-2core`:**
| Workload     | Threads | Dependencies |
| ------------ | ------- | ------------ |
| Memcached    | 1       | None         |
| Blackscholes | 1       | None         |

**Running on `node-b-4core`:**
| Workload | Threads | Dependencies |
| -------- | ------- | ------------ |
| Canneal  | 4       | None         |
| Dedup    | 4       | None         |
| Ferret   | 4       | Dedup        |

**Running on `node-c-8core`:**
| Workload | Threads | Dependencies    |
| -------- | ------- | --------------- |
| Radix    | 8       | None            |
| Freqmine | 8       | Radix           |
| Vips     | 8       | Radix, Freqmine |

## Analyse data

Run the script `extract_info_from_mcperf_logs.py`. It will extract the P95 latency during different time periods from the mcperf logs relative to different runs that are present in `part3_raw_outputs` and save the results in `part3_extracted_data`.

Run the script `extract_info_from_pods_logs.py`. It will extract the execution time, the start time and the stop time of the different workloads from the pods logs relative to different runs that are present in `part3_raw_outputs` and save the results in `part3_extracted_data`.

In `part3_extracted_data` there is a Python script called `analyse_pod_times.py` that will calculate the average execution time and the standard deviation for the different workloads. The outer Python script, called `create_plots.py`, that will plot the P95 latency of memcached in the background and the scheduling of the different workloads on top of it.
