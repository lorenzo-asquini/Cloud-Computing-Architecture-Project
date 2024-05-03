import logging
import docker.models
import docker.models.containers
import psutil
import sys
import docker
from scheduler.enums import JobType, ContainerState
from time import sleep

logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=logging_format)

number_of_cores = psutil.cpu_count()
docker_client = docker.from_env()

logging.info(f"Total number of cores: {number_of_cores}")
logging.info(f"Setting up initial states")

CONTAINERS : dict[str, docker.models.containers.Container] = {
    e.name: None for e in JobType
}


def canStopLoop():
    """ Can break loop if all containers have finished running """
    all_containers_have_started = all(c is not None for c in CONTAINERS.values())

    if not all_containers_have_started:
        return False
    
    container_states = {k: ContainerState.fromStr(c.status) if c else ContainerState.UNKNOWN for k, c in CONTAINERS.items()}
    logging.info(f"Container states: {container_states}")
    
    all_containers_exited = all(state == ContainerState.EXITED for state in container_states.values())
    if not all_containers_exited:
        return False
    
    return True


def canStartContainer(job_type: JobType):
    
    if CONTAINERS[job_type.name]:
        # Already started
        return False
    else:
        return True


def startRun(job_type: JobType):
    return docker_client.containers.run(job_type.value, detach=True)


while True:
    
    if canStopLoop():
        break

    for job_type in JobType:
        if canStartContainer(job_type):

    logging.info(psutil.cpu_percent(interval=1, percpu=True))
    sleep(5)