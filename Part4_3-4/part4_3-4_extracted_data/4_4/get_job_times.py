####################################
# Get average execution time and standard deviation for the different jobs
####################################

import os
from tabulate import tabulate
from datetime import datetime
import numpy as np

def calculate_stats(folder_path):
    jobs = ["blackscholes", "canneal", "dedup", "ferret", "freqmine", "radix", "vips"]

    job_times = {job: {} for job in jobs}
    job_times["all"] = {
        "start": [],
        "end": [],
        "tot_time": [],
    }

    for idx in range(1, 4):
            
        for job in jobs:
            if job != "all":
                
                if not "start" in job_times[job]:
                    job_times[job]["start"] = []
                    
                if not "end" in job_times[job]:
                    job_times[job]["end"] = []

                if not "tot_time" in job_times[job]:
                    job_times[job]["tot_time"] = []

                with open(os.path.join(folder_path, f"jobs_{idx}.txt")) as file:
                    
                    for line in file:
                        if f"start {job}" in line:
                            timestamp = line.strip().split()[0]
                            datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                            epoch_time = int(datetime_obj.timestamp())
                            job_times[job]["start"].append(epoch_time)

                        if f"end {job}" in line:
                            timestamp = line.strip().split()[0]
                            datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                            epoch_time = int(datetime_obj.timestamp())
                            job_times[job]["end"].append(epoch_time)

                job_times[job]["tot_time"].append(job_times[job]["end"][-1] - job_times[job]["start"][-1])

    for idx in range(3):
        all_start = 12345678901234567890
        all_end = 0
        for job in jobs:
            all_start = min(all_start, job_times[job]["start"][idx])
            all_end = max(all_end, job_times[job]["end"][idx])

        job_times["all"]["start"] = all_start
        job_times["all"]["end"] = all_end
        job_times["all"]["tot_time"] = all_end - all_start
        

    for job in job_times:
        job_times[job]["avg_time"] = np.mean(np.array(job_times[job]["tot_time"]))
        job_times[job]["std_time"] = np.std(np.array(job_times[job]["tot_time"]))

    job_times["all"]["std_time"] = np.std(np.array(job_times["all"]["tot_time"]))

    return job_times

    
def main():
    job_times = calculate_stats("../../part4_3-4_raw_outputs/4_4_3s")

    table_data = []
    for job, data in job_times.items():
        avg_time = "{:.2f}".format(data["avg_time"])
        std_time = "{:.2f}".format(data["std_time"])
        table_data.append([job, avg_time, std_time])

    print(tabulate(table_data, headers=["Job", "Avg (s)", "Std (s)"], tablefmt="grid"))

if __name__ == "__main__":
    main()
