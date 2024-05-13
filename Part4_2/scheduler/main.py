import logging
import docker.models
import docker.models.containers
import sys
import docker
from policies import CPUBasedPolicy
from enums import JobContainer, ContainerState
from time import sleep

import scheduler_logger as sl

# The official logger will create its own file, so no need to worry about polluting it
logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=logging_format)

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


def startJob(job_container: JobContainer, run_arguments: str, cores: str, cpu_period: int, coexist: bool):
    if(coexist):
        return docker_client.containers.run(job_container.value, run_arguments, cpuset_cpus=cores, cpu_period=cpu_period, cpu_quota=int(cpu_period/4), detach=True, name=job_container.name)
    else:
        return docker_client.containers.run(job_container.value, run_arguments, cpuset_cpus=cores, detach=True, name=job_container.name)


def main():

    policy = CPUBasedPolicy()

    official_logger = sl.SchedulerLogger()
    official_logger.job_start(sl.Job.MEMCACHED, ["0", "1"], 2)
    
    while True:
        
        ### Check if jobs have exited. If first time, log it
        can_exit = True
        for job_type in sl.Job:
            if job_type.name == "SCHEDULER" or job_type.name == "MEMCACHED":
                continue

            if getContainerStates()[job_type.name] == ContainerState.EXITED:
                if not policy.JOB_INFOS[job_type.name]["Logged_Exit"]:
                    official_logger.job_end(job_type)
                    policy.JOB_INFOS[job_type.name]["Logged_Exit"] = True

                    logging.info(f"Job {job_type.name} just exited")

            else:
                can_exit = False  # At least one job is still running

        if can_exit:
            break


        ### Start new containers if dependencies are satisfied
        for job_type in sl.Job:
            if job_type.name == "SCHEDULER" or job_type.name == "MEMCACHED":
                continue

            ##### Start container if all dependencies have finished and, if coexisting, if memcache load is low enough
            if policy.canRunJob(job_type.name, getContainerStates()):

                container_cores = ",".join(policy.JOB_INFOS[job_type.name]["Cores"])  # From list of cores to comma separated cores
                does_coexist = (policy.JOB_INFOS[job_type.name]["Cores"] == ["1"])

                CONTAINERS[job_type.name] = startJob(JobContainer[job_type.name], policy.getRunArguments(JobContainer[job_type.name]), 
                                                     container_cores, policy.base_job_cpu_period, does_coexist).id

                if(does_coexist):
                    policy.JOB_INFOS[job_type.name]["LastQuotaUpdate"] = int(policy.base_job_cpu_period / 4)

                official_logger.job_start(job_type, policy.JOB_INFOS[job_type.name]["Cores"], policy.JOB_INFOS[job_type.name]["Threads"])
                logging.info(f"Starting job {job_type.name}")
            

            ##### Check if the coexistent job should be stopped or resumed
            possible_quota_change, new_job_cpu_quota = policy.updateJobQuota(job_type.name)

            if(possible_quota_change):

                if(new_job_cpu_quota == 0):

                    # If new cpu quota is 0 and the job is running, pause it
                    if(getContainerStates()[job_type.name] == ContainerState.RUNNING):
                        official_logger.job_pause(job_type)
                        getContainerById(CONTAINERS[job_type.name]).pause()
                        logging.info(f"Pausing job {job_type.name}")

                else:
                    # If the new cpu quota is not 0, if the container is paused, unpause it. Either case, update it's quota
                    if(getContainerStates()[job_type.name] == ContainerState.PAUSED):
                        official_logger.job_unpause(job_type)
                        getContainerById(CONTAINERS[job_type.name]).unpause()
                        logging.info(f"Unpausing job {job_type.name}")

                    if(getContainerStates()[job_type.name] == ContainerState.RUNNING):
                        if(new_job_cpu_quota != policy.JOB_INFOS[job_type.name]["LastQuotaUpdate"]):  # Update only if necessary
                            getContainerById(CONTAINERS[job_type.name]).update(cpu_quota=new_job_cpu_quota)
                            policy.JOB_INFOS[job_type.name]["LastQuotaUpdate"] = new_job_cpu_quota

                            official_logger.custom_event(job_type, f"Job quota percentage {100*new_job_cpu_quota/policy.base_job_cpu_period:.1f}")
                            logging.info(f"New job quota for {job_type.name} is {100*new_job_cpu_quota/policy.base_job_cpu_period:.1f}%")

        sleep(0.2)  # Act fast because load can change rapidly

    official_logger.end()

    # Give 2 cores to memcache before exiting
    policy.setMemcacheTwoCores()


if __name__ == "__main__":
   main()