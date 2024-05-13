from enums import ContainerState, JobContainer

import os
import psutil

class Policy:
    
    RUN_ARGUMENTS = {}

    JOB_INFOS = {}

    @classmethod
    def getRunArguments(cls, job_type: JobContainer):
        if job_type not in cls.RUN_ARGUMENTS:
            raise RuntimeError(f"Could not find runtime arguments for job: {job_type}")
        return cls.RUN_ARGUMENTS[job_type] + str(cls.JOB_INFOS[job_type.name]["Threads"])

    def canRunJob(self, job_type: JobContainer, container_states: dict[str, ContainerState]):
        raise NotImplementedError()
    

class CPUBasedPolicy(Policy):

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
        "RADIX": {
            "Cores": ["1"],
            "Dependencies": [],
            "Threads": 1,
            "Logged_Exit": False
        },

        "BLACKSCHOLES": {
            "Cores": ["2", "3"],
            "Dependencies": [],
            "Threads": 2,
            "Logged_Exit": False
        },
        "FERRET": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES"],
            "Threads": 2,
            "Logged_Exit": False
        },
        "FREQMINE": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET"],
            "Threads": 2,
            "Logged_Exit": False
        },
        "VIPS": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET", "FREQMINE"],
            "Threads": 2,
            "Logged_Exit": False
        },
        "CANNEAL": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET", "FREQMINE", "VIPS"],
            "Threads": 2,
            "Logged_Exit": False
        },
        "DEDUP": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET", "FREQMINE", "VIPS", "CANNEAL"],
            "Threads": 2,
            "Logged_Exit": False
        },
    }

    def __init__(self):
        memcache_pid = int(os.popen("cat /var/run/memcached/memcached.pid").read().strip())
        self.memcache_process = psutil.Process(memcache_pid)
    
    
    def canRunJob(self, job_type: str, all_container_states: dict[str, ContainerState]):
        """
        If the job already started, it cannot be started again.

        If all the dependencies exited, start the job.

        Return True if the job was started, False otherwise.
        """

        # If the container state is not unknown, then it was started at some point
        if all_container_states[job_type] != ContainerState.UNKNOWN:
            return False
        
        # Check for all Dependencies
        can_start = True
        for dependency in self.JOB_INFOS[job_type]["Dependencies"]:
            if(all_container_states[dependency] != ContainerState.EXITED):
                can_start = False
                break

        cpu_usage = self.memcache_process.cpu_percent(interval=0.2)
        if(cpu_usage > 35 and self.JOB_INFOS[job_type]["Cores"] == ["1"]):  # Do not start a coexisting job if memcache is under load
            can_start = False 

        return can_start
    
    
    base_job_cpu_period = 50000  # CPU period of a job. Used to lower the quota of a job in shared core with memcache
    def updateJobQuota(self, job_type: str):
        """
        Handle the potential Coexistence of a job in the core 1 with memcache.

        If memcache starts using two cores, start lowering the cpu quota of the coexisting job until it's necessary to stop it.

        It returns True if the quota of the job may be changed, False if the job is not coexisting with memcache.
        """

        if(self.JOB_INFOS[job_type]["Cores"] == ["1"]):
            cpu_usage = self.memcache_process.cpu_percent(interval=0.2)

            # Interpolate the quota (from 2000 to the cpu period) depending on the CPU usage of memcache
            stop_coexisting_th = 35
            min_quota = 2000

            if(cpu_usage < stop_coexisting_th):

                # Calculate the ratio of cpu that should be left to memcache
                ratio = cpu_usage / stop_coexisting_th

                # Make sure it doesn't go above the cpu period
                new_quota = min(self.base_job_cpu_period, (self.base_job_cpu_period - min_quota) * (1-ratio) + min_quota)

            if(cpu_usage >= stop_coexisting_th):
                new_quota = 0  # Pause the job

            return True, int(new_quota)
            
        return False, None