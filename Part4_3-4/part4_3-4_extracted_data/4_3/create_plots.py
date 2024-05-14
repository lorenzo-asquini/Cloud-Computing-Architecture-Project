import matplotlib.pyplot as plt
from datetime import datetime

colors = {
    "blackscholes": "#CCA000",
    "canneal": "#CCCCAA",
    "dedup": "#CCACCA",
    "ferret": "#AACCCA",
    "freqmine": "#0CCA00",
    "radix": "#00CCA0",
    "vips": "#CC0A00"
    }

workload_labels = {
    "blackscholes": "Blackscholes",
    "canneal": "Canneal",
    "dedup": "Dedup",
    "ferret": "Ferret",
    "freqmine": "Freqmine",
    "radix": "Radix",
    "vips": "Vips"
    }

def extract_memcache_data(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Extract start and end timestamps
    start_timestamp = None
    end_timestamp = None
    for line in lines:
        if line.startswith("Timestamp start:"):
            start_timestamp = int(line.split(":")[1].strip())
        elif line.startswith("Timestamp end:"):
            end_timestamp = int(line.split(":")[1].strip())
            break

    # Extract p95 values and QPS values for lines starting with "read"
    data = {"timestamp": [], "p95": [], "qps": []}
    for i, line in enumerate(lines):
        if line.startswith("read"):
            tokens = line.split()
            data["timestamp"].append(start_timestamp + i * 10000)
            data["p95"].append(float(tokens[12]))
            data["qps"].append(float(tokens[16]))

    return start_timestamp, end_timestamp, data

def extract_jobs_data(file_path):
    jobs = ["blackscholes", "canneal", "dedup", "ferret", "freqmine", "radix", "vips"]

    job_times = {job: {} for job in jobs}
    
    for job in jobs:

        if not "pause" in job_times[job]:
            job_times[job]["pause"] = []
            
        if not "unpause" in job_times[job]:
            job_times[job]["unpause"] = []
            
        with open(file_path, 'r') as file:
            
            for line in file:
                if f"start {job}" in line:
                    timestamp = line.strip().split()[0]
                    datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                    epoch_time = int(datetime_obj.timestamp()) * 1000 + 2 * 3600000
                    job_times[job]["start"] = epoch_time

                if f"end {job}" in line:
                    timestamp = line.strip().split()[0]
                    datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                    epoch_time = int(datetime_obj.timestamp()) * 1000 + 2 * 3600000
                    job_times[job]["end"] = epoch_time

                if f"pause {job}" in line:
                    timestamp = line.strip().split()[0]
                    datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                    epoch_time = int(datetime_obj.timestamp()) * 1000 + 2 * 3600000
                    job_times[job]["pause"].append(epoch_time)

                if f"unpause {job}" in line:
                    timestamp = line.strip().split()[0]
                    datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                    epoch_time = int(datetime_obj.timestamp()) * 1000 + 2 * 3600000
                    job_times[job]["unpause"].append(epoch_time)

    memcache_cores = {"timestamp": [], "cores": []}
    with open(file_path, 'r') as file:
        for line in file:
            if "start memcached" in line:
                timestamp = line.strip().split()[0]
                datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                epoch_time = int(datetime_obj.timestamp()) * 1000 + 2 * 3600000
                memcache_cores["timestamp"].append(epoch_time)
                memcache_cores["cores"].append(2)

            if "update_cores memcached" in line:
                timestamp = line.strip().split()[0]
                datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                epoch_time = int(datetime_obj.timestamp()) * 1000 + 2 * 3600000
                memcache_cores["timestamp"].append(epoch_time)
                
                if "[0]" in line:
                    memcache_cores["cores"].append(1)
                else:
                    memcache_cores["cores"].append(2)

            if "end scheduler" in line:
                timestamp = line.strip().split()[0]
                datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                epoch_time = int(datetime_obj.timestamp()) * 1000 + 2 * 3600000
                memcache_cores["timestamp"].append(epoch_time)
                memcache_cores["cores"].append(2)

    return job_times, memcache_cores

for idx in range(1, 4):
    # Print the extracted data
    start_timestamp, end_timestamp, memcache_data = extract_memcache_data(f"../../part4_3-4_raw_outputs/4_3/mcperf_{idx}.txt")
    job_times, memcache_cores = extract_jobs_data(f"../../part4_3-4_raw_outputs/4_3/jobs_{idx}.txt")
    # Plotting
    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('P95', color=color)
    ax1.plot(memcache_data["timestamp"], memcache_data["p95"], color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  
    color = 'tab:blue'
    ax2.set_ylabel('QPS', color=color)
    ax2.plot(memcache_data["timestamp"], memcache_data["qps"], color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  
    plt.show()

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Cores', color=color)
    ax1.step(memcache_cores["timestamp"], memcache_cores["cores"], where='post', color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  
    color = 'tab:blue'
    ax2.set_ylabel('QPS', color=color)
    ax2.plot(memcache_data["timestamp"], memcache_data["qps"], color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  
    plt.show()
