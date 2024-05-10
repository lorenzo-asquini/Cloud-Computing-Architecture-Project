from scheduler.enums import ContainerState, JobContainer
from scheduler_logger import Job

import os
import psutil

class Policy:
    
    RUN_ARGUMENTS = {}

    JOB_INFOS = {}

    @classmethod
    def getRunArguments(cls, job_type: JobContainer):
        if job_type not in cls.RUN_ARGUMENTS:
            raise RuntimeError(f"Could not find runtime arguments for job: {job_type}")
        return cls.RUN_ARGUMENTS[job_type]

    def canRunJob(self, job_type: JobContainer, container_states: dict[str, ContainerState]):
        raise NotImplementedError()
    
    def adjustMemcacheCores(self):
        raise NotImplementedError()
    
    def pauseJob(self):
        raise NotImplementedError()


class CPUBasedPolicy(Policy):

    # Initial idea:
    # Use the two cores that are never used by memcache to run in order: Ferret, Freqmine, Radix, Vips
    # Once they are done, start in parallel on those two cores: Canneal, Dedup
    # Keep Blackscholes running on the second core that may be used by Memcache. If the CPU usage is very high, pause it.
    # TODO: Possibly, if Blackscholes finishes early, use the core for someone else + Parallelize something else

    # Threads are set dynamically
    RUN_ARGUMENTS = {
        JobContainer.BLACKSCHOLES: "./run -a run -S parsec -p blackscholes -i native -n ",

        JobContainer.FERRET: "./run -a run -S parsec -p ferret -i native -n ",
        JobContainer.FREQMINE: "./run -a run -S parsec -p freqmine -i native -n ",
        JobContainer.RADIX: "./run -a run -S splash2x -p radix -i native -n ",
        JobContainer.VIPS: "./run -a run -S parsec -p vips -i native -n ",

        JobContainer.CANNEAL: "./run -a run -S parsec -p canneal -i native -n ",
        JobContainer.DEDUP: "./run -a run -S parsec -p dedup -i native -n ",
    }

    JOB_INFOS = {
        Job.BLACKSCHOLES: {
            "CORES": ["1"],
            "DEPENDENCIES": [],
            "THREADS": 1,
            "COEXIST": True,
            "LOGGED_EXIT": False
        },

        Job.FERRET: {
            "CORES": ["2", "3"],
            "DEPENDENCIES": [],
            "THREADS": 2,
            "COEXIST": False,
            "LOGGED_EXIT": False
        },
        Job.FREQMINE: {
            "CORES": ["2", "3"],
            "DEPENDENCIES": [Job.FERRET],
            "THREADS": 2,
            "COEXIST": False,
            "LOGGED_EXIT": False
        },
        Job.RADIX: {
            "CORES": ["2", "3"],
            "DEPENDENCIES": [Job.FERRET, Job.FREQMINE],
            "THREADS": 2,
            "COEXIST": False,
            "LOGGED_EXIT": False
        },
        Job.VIPS: {
            "CORES": ["2", "3"],
            "DEPENDENCIES": [Job.FERRET, Job.FREQMINE, Job.RADIX],
            "THREADS": 2,
            "COEXIST": False,
            "LOGGED_EXIT": False
        },

        Job.CANNEAL: {
            "CORES": ["2", "3"],
            "DEPENDENCIES": [Job.FERRET, Job.FREQMINE, Job.RADIX, Job.VIPS],
            "THREADS": 2,
            "COEXIST": False,
            "LOGGED_EXIT": False
        },
        Job.DEDUP: {
            "CORES": ["2", "3"],
            "DEPENDENCIES": [Job.FERRET, Job.FREQMINE, Job.RADIX, Job.VIPS],
            "THREADS": 2,
            "COEXIST": False,
            "LOGGED_EXIT": False
        },   
    }

    current_memcache_cores = 2 # The starting value is always 2

    def __init__(self):
        memcache_pid = int(os.popen("cat /var/run/memcached/memcached.pid").read().strip())
        self.memcache_process = psutil.Process(memcache_pid)

    def adjustMemcacheCores(self):
        """
        Adjust the number of cores assigned to memcache.

        If the number of cores is 1 and the cpu utilization is above 30%, switch to two cores.
        If the number of cores is 2 and the cpu utilization is below 40%, switch to one core.

        Return the new number of cores if there was a change, -1 otherwise.
        """

        cpu_usage = self.memcache_process.cpu_percent(interval=0.4)

        # If using 2 cores and the cpu is below 40%, switch to 1 core
        if(cpu_usage < 40 and self.current_memcache_cores == 2):
            self.memcache_process.cpu_affinity([0])  # TODO: Does this work as taskset?
            return 1
        
        # If using 1 core and the cpu is above 30%, switch to 2 cores
        if(cpu_usage > 30 and self.current_memcache_cores == 1):
            self.memcache_process.cpu_affinity([0, 1])
            return 2
        
        return -1  # No change
    
    def canRunJob(self, job_type: Job, all_container_states: dict[str, ContainerState]):
        """
        If the job already started, it cannot be started again.
        If all the dependencies exited, start the job.
        Return True if the job started, False otherwise.
        """

        # If the container state is not None or if it's in progress, cannot start the job
        if not all_container_states[job_type] or ContainerState.isInProgress(all_container_states[job_type]):
            return False
        
        # Check for all dependencies
        can_start = True
        for dependency in self.JOB_INFOS[job_type]["DEPENDENCIES"]:
            if(all_container_states[dependency] != ContainerState.EXITED):
                can_start = False
                break
            
        return can_start
    
    def pauseJob(self, job_type: Job):  # TODO: see if it makes sense. See if 150 is a good threshold
        """
        Handle the potential coexistence of a job in the core 1 with memcache.
        If memcache is heavily utilized (cpu > 150%), it's better to stop the job temporarily.
        Return False if there is no coexistence or if the job shouldn't be stopped (resume it if necessary), True if the state should be stopped
        """
        if(self.JOB_INFOS[job_type]["COEXIST"]):
            cpu_usage = self.memcache_process.cpu_percent(interval=0.4)

            if(cpu_usage > 150):
                return True
            else:
                return False
            
        return False