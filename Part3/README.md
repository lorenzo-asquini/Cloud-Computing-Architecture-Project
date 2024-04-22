## YAML files

The YAML files used to execute the tests for Part 3 are contained in the folder `part3 yaml files`. Apart from the files required to run the benchmarks and memcached, there are two versions of the file used to create the cluster. `part3.yaml` is the official file and the one that needs to be used for the submission. `part3_cheap.yaml` is a copy of `part3.yaml` where all the machines used in the cluster are cheap. Considering that the various machines required are quite expensive, it does not make sense to waste credits while testing the automatic scripts. Both files require modifying some values according to the configuration.

Inside each YAML file that contains a `Job` or a `Pod` change the value associated to `spec/nodeSelector/cca-project-nodetype` according to which one should be the node where that job or pod should run. The options are: `node-a-2core`, `node-b-4core` and `node-c-8core`.

For the benchmarks, it's possible to change the number of cores to use by changing the number that comes after the flag `-n` in the value associated to `spec/template/spec/containers/args`.