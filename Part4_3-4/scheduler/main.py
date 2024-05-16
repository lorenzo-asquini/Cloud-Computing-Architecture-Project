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


def startJob(job_container: JobContainer, run_arguments: str, cores: str, cpu_period: int, cpu_quota: int):
    return docker_client.containers.run(job_container.value, run_arguments, cpuset_cpus=cores, cpu_period=cpu_period, cpu_quota=cpu_quota, detach=True, name=job_container.name)
    

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


        ### Adjust the number of cores of memcache and log the change (if any)
        new_memcache_cores = policy.adjustMemcacheCores()
        if(new_memcache_cores == 1):
            official_logger.update_cores(sl.Job.MEMCACHED, ["0"])
            logging.info("Updating memcache cores to 1 only")
        elif(new_memcache_cores == 2):
            official_logger.update_cores(sl.Job.MEMCACHED, ["0", "1"])
            logging.info("Updating memcache cores to 2")


        ### Handle jobs lives
        for job_type in sl.Job:
            if job_type.name == "SCHEDULER" or job_type.name == "MEMCACHED":
                continue

            if policy.canRunJob(job_type.name, getContainerStates()):
            
                # Always give 2 cores to memcache when a new job starts
                if(policy.current_memcache_cores != 2):
                    policy.setMemcacheTwoCores()
                    official_logger.update_cores(sl.Job.MEMCACHED, ["0", "1"])
                    logging.info("Updating memcache cores to 2")

                container_cores = ",".join(policy.JOB_INFOS[job_type.name]["Cores"])  # From list of cores to comma separated cores

                CONTAINERS[job_type.name] = startJob(JobContainer[job_type.name], policy.getRunArguments(JobContainer[job_type.name]), 
                                                     container_cores, policy.base_job_cpu_period, policy.JOB_INFOS[job_type.name]["Starting_Quota"]).id

                official_logger.job_start(job_type, policy.JOB_INFOS[job_type.name]["Cores"], policy.JOB_INFOS[job_type.name]["Threads"])
                logging.info(f"Starting job {job_type.name}")
            

            ##### Update quotas
            new_job_cpu_quota = policy.updateJobQuota(job_type.name)

            # If the job coexists with memcache
            if(policy.JOB_INFOS[job_type.name]["Cores"] == ["1"]):

                if(new_job_cpu_quota == 0):
                    # If new cpu quota is 0 and the job is running, pause it
                    if(getContainerStates()[job_type.name] == ContainerState.RUNNING):
                        official_logger.job_pause(job_type)
                        getContainerById(CONTAINERS[job_type.name]).pause()
                        logging.info(f"Pausing job {job_type.name}")

                else:
                    # If the new cpu quota is not 0, if the container is paused, unpause it
                    if(getContainerStates()[job_type.name] == ContainerState.PAUSED):
                        official_logger.job_unpause(job_type)
                        getContainerById(CONTAINERS[job_type.name]).unpause()
                        logging.info(f"Unpausing job {job_type.name}")


            # Update the job quota if necessary
            if(getContainerStates()[job_type.name] == ContainerState.RUNNING):
                if(new_job_cpu_quota != policy.JOB_INFOS[job_type.name]["Current_Quota"]):  # Update only if necessary

                    getContainerById(CONTAINERS[job_type.name]).update(cpu_quota=new_job_cpu_quota)
                    policy.JOB_INFOS[job_type.name]["Current_Quota"] = new_job_cpu_quota

                    official_logger.custom_event(job_type, f"Job quota percentage {100*new_job_cpu_quota/policy.base_job_cpu_period:.1f}")
                    logging.info(f"New job quota for {job_type.name} is {100*new_job_cpu_quota/policy.base_job_cpu_period:.1f}%")

        sleep(1.5)  # Have a relatively large sleep to avoid having the scheduler using too much CPU

    # Give 2 cores to memcache before exiting
    if(policy.current_memcache_cores != 2):
        policy.setMemcacheTwoCores()
        official_logger.update_cores(sl.Job.MEMCACHED, ["0", "1"])
        logging.info("Updating memcache cores to 2")

    official_logger.end()


if __name__ == "__main__":
   main()