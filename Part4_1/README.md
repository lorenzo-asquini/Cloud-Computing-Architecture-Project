## YAML files

The YAML files used to execute the tests for Part 4.1 are contained in the folder `part4_1_yaml_files`. There are two versions of the file used to create the cluster. `part4.yaml` is the official file and the one that needs to be used for the submission. `part4_cheap.yaml` is a copy of `part4.yaml` where all the machines used in the cluster are cheap. Considering that the various machines required are quite expensive, it does not make sense to waste credits while testing the automatic scripts. Both files require modifying some values according to the configuration.

## Analyse data

Run the script `extract_info_from_logs.py`. It will extract the average QPS and its standard deviation, the average P95 latency and its standard deviation, and the average CPU usage during each period considered (for each average achieved QPS, there is an average CPU usage).

In `part4_1_extracted_data` there is a Python script called `create_plot_memcache_only.py` that will plot the average P95 latency at different values of QPS varying the number of cores and threads used. The Python script called `create_plot_with_cpu.py` will plot the average P95 latency at different values of QPS while also displaying the average CPU usage at those QPS values.