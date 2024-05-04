from scheduler.enums import ContainerState, JobType


class Policy:
    
    RUN_ARGUMENTS = {}

    @classmethod
    def getRunArguments(cls, job_type: JobType):
        if job_type not in cls.RUN_ARGUMENTS:
            raise RuntimeError(f"Could not find runtime arguments for job: {job_type}")
        return cls.RUN_ARGUMENTS[job_type]

    def canRunJob(job_type: JobType, container_states: dict[str, ContainerState]):
        raise NotImplementedError()


class OneAtATime(Policy):

    # Policy 0
    
    RUN_ARGUMENTS = {
        JobType.BLACKSCHOLES: "./run -a run -S parsec -p blackscholes -i native -n 2"
    }

    def canRunJob(job_type: JobType, container_states: dict[str, ContainerState]):

        if any(ContainerState.isInProgress(state) for state in container_states.values()):
            return False
        
        return True
    

ARG_TO_POLICY = {
    0: OneAtATime
}