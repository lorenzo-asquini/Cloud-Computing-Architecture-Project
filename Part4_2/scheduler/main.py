import logging
import docker.models
import docker.models.containers
import sys
import docker
from scheduler.policies import CPUBasedPolicy
from scheduler.enums import JobContainer, ContainerState
from time import sleep

import scheduler_logger as sl

# The official logger will create its own file, so no need to worry about polluting it
logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=logging_format)

logging.info("Starting everything")

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


def startJob(job_container: JobContainer, run_arguments: str, cores: str):
    return docker_client.containers.run(job_container.value, run_arguments, cpuset_cpus=cores, detach=True)


def main():

    policy = CPUBasedPolicy()

    official_logger = sl.SchedulerLogger()
    official_logger.job_start(sl.Job.MEMCACHED, ["0", "1"], 2)  # TODO: remember to start memcached with 2 cores at the beginning. In case lower them later
    
    while True:
        
        ### Check if jobs have exited. If first time, log it
        container_states = getContainerStates()

        can_exit = True
        for job_type in sl.Job:
            if container_states[job_type] == ContainerState.EXITED:
                if not policy.JOB_INFOS["LOGGED_EXIT"]:
                    sl.job_end(job_type)
                    policy.JOB_INFOS["LOGGED_EXIT"] = True

                    logging.info(f"Job {job_type} just exited")

            else:
                can_exit = False  # At least one job is still running

        if can_exit:
            break

        ### Adjust the number of cores of memcache and log the change (if any)
        new_memcache_cores = policy.adjustMemcacheCores()
        if(new_memcache_cores == 1):
            official_logger.update_cores(sl.Job.MEMCACHED, ["0"])
            logging.info("Updating memcache cores to 1 only")
        elif(new_memcache_cores == 2):
            official_logger.update_cores(sl.Job.MEMCACHED, ["0", "1"])
            logging.info("Updating memcache cores to 2")

        ### Start new containers if dependencies are satisfied
        for job_type, job_container in zip(sl.Job, JobContainer):

            ##### Start container if all dependencies have finished
            if policy.canRunJob(job_type, getContainerStates()):

                official_logger.job_start(job_type, policy.JOB_INFOS["CORES"], policy.JOB_INFOS["THREADS"])

                container_cores = ",".join(policy.JOB_INFOS["CORES"])  # From list of cores to comma separated cores
                CONTAINERS[job_type.name] = startJob(job_container, 
                                                     policy.getRunArguments(job_container)+str(policy.JOB_INFOS[job_type]), 
                                                     container_cores).id
                
                logging.info(f"Starting job {job_type}")
            

            ##### Check if the coexistent job should be stopped or resumed
            do_pause_job = policy.pauseJob(job_type)

            if(do_pause_job and getContainerStates()[job_type] == ContainerState.RUNNING):
                official_logger.job_pause(job_type)
                getContainerById(CONTAINERS[job_type]).pause()
                logging.info(f"Pausing job {job_type}")

            if(not do_pause_job and getContainerStates()[job_type] == ContainerState.PAUSED):
                official_logger.job_unpause(job_type)
                getContainerById(CONTAINERS[job_type]).unpause()
                logging.info(f"Unpausing job {job_type}")

        sleep(0.5)  # Act quite fast because load can change rapidly


if __name__ == "__main__":
   main()