import logging
import docker.models
import docker.models.containers
import psutil
import sys, getopt
import docker
from scheduler.policies import ARG_TO_POLICY, Policy
from scheduler.enums import JobContainer, ContainerState
from time import sleep

import scheduler_logger as sl

# The official logger will create its own file, so no need to worry about polluting it
logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=logging_format)

logging.info(f"Setting up initial states")


docker_client = docker.from_env()

# Each pair is composed by the Job type and its id (the id is assigned when the container is first started)
CONTAINERS : dict[str, str] = {
    e.name: None for e in sl.Job
}


def getContainerById(containerId) -> docker.models.containers.Container:
    return docker_client.containers.get(containerId)


def getContainerStates():  # Return a dict that assigns to each Job type it's state
    return {
        k: ContainerState.fromStr(getContainerById(c_id).status) if c_id else ContainerState.UNKNOWN 
        for k, c_id in CONTAINERS.items()
    }


def canStopLoop():
    """ Can break loop if all containers have finished running """
    all_containers_have_started = all(c is not None for c in CONTAINERS.values())

    container_states = getContainerStates()
    ### logging.info(f"Container states: {container_states}")

    if not all_containers_have_started:
        return False

    all_containers_exited = all(state == ContainerState.EXITED for state in container_states.values())
    if not all_containers_exited:
        return False
    
    return True


def canStartContainer(job_type: sl.Job, policy: Policy):
    
    if CONTAINERS[job_type.name]:
        # Already started
        return False
    else:
        return policy.canRunJob(job_type, getContainerStates())


def startRun(job_container: JobContainer, run_arguments: str, cores: str):
    return docker_client.containers.run(job_container.value, run_arguments, cpuset_cpus=cores, detach=True)


def main(argv):
    # default policy:
    policy_id = 0

    # parse command line options:
    try:
       opts, args = getopt.getopt(argv,"p:",["policy="])
    except getopt.GetoptError:
       sys.exit(2)

    for opt, arg in opts:
       if opt in ("-p", "--policy"):
          # use alternative policy:
          policy_id = arg

    policy: Policy = ARG_TO_POLICY[policy_id]
    logging.info(f"Using resource scheduling policy: {policy.__name__}")

    official_logger = sl.SchedulerLogger()
    official_logger.job_start(sl.Job.MEMCACHED, ["0", "1"], 2)  # TODO: remember to start memcached with 2 cores at the beginning. In case lower them later
    
    while True:
        
        if canStopLoop():
            break

        # Adjust the number of cores of memcache and log the change (if any)
        new_memcache_cores = policy.adjustMemcacheCores()
        if(new_memcache_cores == 1):
            official_logger.update_cores(sl.Job.MEMCACHED, ["0"])
            logging.info("Updating memcache cores to 1 only")
        elif(new_memcache_cores == 2):
            official_logger.update_cores(sl.Job.MEMCACHED, ["0", "1"])
            logging.info("Updating memcache cores to 2")

        # Start new containers if dependencies are satisfied
        for job_type, job_container in zip(sl.Job, JobContainer):

            # Start container if all dependencies have finished
            if canStartContainer(job_type, policy):

                official_logger.job_start(job_type, policy.JOB_INFOS["CORES"], policy.JOB_INFOS["THREADS"])

                container_cores = ",".join(policy.JOB_INFOS["CORES"])
                CONTAINERS[job_type.name] = startRun(job_container, 
                                                     policy.getRunArguments(job_container)+str(policy.JOB_INFOS[job_type]), 
                                                     container_cores).id
                
                logging.info(f"Starting job {job_type}")  # TODO: Does it work like this?
            
            # Check if the coexistent job should be stopped
            do_pause_job = policy.pauseJob(job_type)

            if(do_pause_job and getContainerStates()[job_type] == ContainerState.RUNNING):
                official_logger.job_pause(job_type)
                getContainerById(CONTAINERS[job_type]).pause()
                logging.info(f"Pausing job {job_type}")  # TODO: Does it work like this?

            if(not do_pause_job and getContainerStates()[job_type] == ContainerState.PAUSED):
                official_logger.job_unpause(job_type)
                getContainerById(CONTAINERS[job_type]).unpause()
                logging.info(f"Unpausing job {job_type}")  # TODO: Does it work like this?

            # TODO: Log when jobs finish (only once)

        sleep(0.5)  # Act quite fast because load can change rapidly


if __name__ == "__main__":
   main(sys.argv[1:])