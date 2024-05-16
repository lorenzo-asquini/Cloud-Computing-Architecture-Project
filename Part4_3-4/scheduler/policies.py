from enums import ContainerState, JobContainer
from scheduler_logger import Job

import os
import psutil

class Policy:
    
    RUN_ARGUMENTS = {}

    @classmethod
    def getRunArguments(cls, job_type: JobContainer):
        if job_type not in cls.RUN_ARGUMENTS:
            raise RuntimeError(f"Could not find runtime arguments for job: {job_type}")
        return cls.RUN_ARGUMENTS[job_type] + str(cls.JOB_INFOS[job_type.name]["Threads"])

    def canRunJob(self, job_type: JobContainer, container_states: dict[str, ContainerState]):
        raise NotImplementedError()
    
    def adjustMemcacheCores(self):
        raise NotImplementedError()
    
    def updateJobQuota(self):
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

    # Define the number of cores, the number of threads and the dependencies of each job
    JOB_INFOS = {
        "RADIX": {
            "Cores": ["1"],
            "Dependencies": [],
            "Threads": 1
        },

        "BLACKSCHOLES": {
            "Cores": ["2", "3"],
            "Dependencies": [],
            "Threads": 2
        },
        "FERRET": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES"],
            "Threads": 2
        },
        "FREQMINE": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET"],
            "Threads": 2
        },
        "CANNEAL": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET", "FREQMINE"],
            "Threads": 2
        },
        "DEDUP": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET", "FREQMINE", "CANNEAL"],
            "Threads": 2
        },
        "VIPS": {
            "Cores": ["2", "3"],
            "Dependencies": ["BLACKSCHOLES", "FERRET", "FREQMINE", "CANNEAL", "DEDUP"],
            "Threads": 2
        },
    }

    base_job_cpu_period = 50000  # CPU period of a job. Used to change the quota of a job


    def __init__(self):
        memcache_pid = int(os.popen("cat /var/run/memcached/memcached.pid").read().strip())
        self.memcache_process = psutil.Process(memcache_pid)

        for job_type in self.JOB_INFOS:
            self.JOB_INFOS[job_type]["Logged_Exit"] = False

            # Start the jobs slowly to not stress too much memcached
            self.JOB_INFOS[job_type]["Maximum_Quota"] = int(self.base_job_cpu_period * len(self.JOB_INFOS[job_type]["Cores"]))
            self.JOB_INFOS[job_type]["Starting_Quota"] = int(self.JOB_INFOS[job_type]["Maximum_Quota"] / 2)
            self.JOB_INFOS[job_type]["Delta_Quota"] = int((self.JOB_INFOS[job_type]["Maximum_Quota"] - self.JOB_INFOS[job_type]["Starting_Quota"]) / 20)
            self.JOB_INFOS[job_type]["Current_Quota"] = self.JOB_INFOS[job_type]["Starting_Quota"]


    ### Handle memcache cores
    current_memcache_cores = 2 # The starting value is always 2
    change_memcache_cores_th = 20


    def setMemcacheTwoCores(self):
        self.memcache_process.cpu_affinity([0, 1])
    def setMemcacheOneCore(self):
        self.memcache_process.cpu_affinity([0])


    def adjustMemcacheCores(self):
        """
        Adjust the number of cores assigned to memcache.

        If the number of cores is 1 and the cpu utilization is above threshold, switch to two cores.
        If the number of cores is 2 and the cpu utilization is below threshold, switch to one core.

        Return the new number of cores if there was a change, -1 otherwise.
        """

        cpu_usage = self.memcache_process.cpu_percent(interval=0.2)

        # If using 2 cores and the cpu is below threshold, switch to 1 core
        if(cpu_usage < self.change_memcache_cores_th and self.current_memcache_cores == 2):
            self.memcache_process.cpu_affinity([0])  # Requires execution with sudo
            self.current_memcache_cores = 1
            return 1
        
        # If using 1 core and the cpu is above threshold, switch to 2 cores
        if(cpu_usage > self.change_memcache_cores_th and self.current_memcache_cores == 1):
            self.memcache_process.cpu_affinity([0, 1])
            self.current_memcache_cores = 2
            return 2
        
        return -1  # No change
    

    ### Decide if it's possible to run a job
    def canRunJob(self, job_type: str, all_container_states: dict[str, ContainerState]):
        """
        If the job already started, it cannot be started again.

        If all the dependencies exited, and memcache is not under heavy load, start the job.

        Return True if the job was started, False otherwise.
        """

        # If the container state is not unknown, then it was started at some point
        if all_container_states[job_type] != ContainerState.UNKNOWN:
            return False
        
        # Check for all dependencies
        can_start = True
        for dependency in self.JOB_INFOS[job_type]["Dependencies"]:
            if(all_container_states[dependency] != ContainerState.EXITED):
                can_start = False
                break

        # Do not start a job if memcache is under heavy load
        cpu_usage = self.memcache_process.cpu_percent(interval=0.2)
        if(cpu_usage > 75):  
            can_start = False 

        return can_start
    

    ### Handle job CPU quotas
    def updateJobQuota(self, job_type: str):
        """
        If a job is not coexisting with memcache, increase its quota if it's lower than the maximum.
        If a job is coexisting with memcache, change its quota depending on the load on memcache.

        Return the new quota (that may or may not be applied)
        """

        # Coexisting job
        if(self.JOB_INFOS[job_type]["Cores"] == ["1"]):
            cpu_usage = self.memcache_process.cpu_percent(interval=0.2)

            # Interpolate the quota depending on the CPU usage of memcache
            stop_coexisting_th = 50
            safe_coexist_th = 10

            min_quota = 2000
            max_quota = self.JOB_INFOS[job_type]["Maximum_Quota"]

            if(cpu_usage < safe_coexist_th):
                new_quota = max_quota  # Keep the quota at the maximum if memcache is not used much

            if(cpu_usage >= safe_coexist_th and cpu_usage < stop_coexisting_th):

                # Calculate the ratio of cpu that should be left to memcache
                ratio = (cpu_usage - safe_coexist_th) / (stop_coexisting_th - safe_coexist_th)

                # Make sure it doesn't go above the maximum
                new_quota = min(max_quota, (max_quota - min_quota) * (1-ratio) + min_quota)

            if(cpu_usage >= stop_coexisting_th):
                new_quota = 0  # Pause the job
            
        else:

            # Increase little by little the quota to reach the maximum quota
            new_quota = min(self.JOB_INFOS[job_type]["Maximum_Quota"], self.JOB_INFOS[job_type]["Current_Quota"] + self.JOB_INFOS[job_type]["Delta_Quota"])

        return int(new_quota)
