import logging
import docker.models
import docker.models.containers
import psutil
import sys, getopt
import docker
from scheduler.policies import ARG_TO_POLICY, Policy
from scheduler.enums import JobType, ContainerState
from time import sleep

logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=logging_format)

number_of_cores = psutil.cpu_count()
docker_client = docker.from_env()

logging.info(f"Total number of cores: {number_of_cores}")
logging.info(f"Setting up initial states")


CONTAINERS : dict[str, str] = {
    e.name: None for e in JobType
}


def getContainerById(containerId) -> docker.models.containers.Container:
    return docker_client.containers.get(containerId)


def getContainerStates():
    return {
        k: ContainerState.fromStr(getContainerById(c_id).status) if c_id else ContainerState.UNKNOWN 
        for k, c_id in CONTAINERS.items()
    }


def canStopLoop():
    """ Can break loop if all containers have finished running """
    all_containers_have_started = all(c is not None for c in CONTAINERS.values())

    container_states = getContainerStates()
    logging.info(f"Container states: {container_states}")

    if not all_containers_have_started:
        return False

    all_containers_exited = all(state == ContainerState.EXITED for state in container_states.values())
    if not all_containers_exited:
        return False
    
    return True


def canStartContainer(job_type: JobType, policy: Policy):
    
    if CONTAINERS[job_type.name]:
        # Already started
        return False
    else:
        return policy.canRunJob(job_type, getContainerStates())


def startRun(job_type: JobType, run_arguments: str):
    return docker_client.containers.run(job_type.value, run_arguments, detach=True)


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

    while True:
        
        if canStopLoop():
            break

        for job_type in JobType:
            if canStartContainer(job_type, policy):
                logging.info(f"Starting run {job_type.name}")
                CONTAINERS[job_type.name] = startRun(job_type, policy.getRunArguments(job_type)).id

        logging.info(f"TOTAL CPU USAGE: {psutil.cpu_percent()}")
        logging.info(f"CPU USAGE PER CORE: {psutil.cpu_percent(interval=1, percpu=True)}")
        sleep(5)


if __name__ == "__main__":
   main(sys.argv[1:])