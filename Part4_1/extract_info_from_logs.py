######
# Raw logs in folder "part4_1_raw_outputs".
# Each file with memcache data should be named with the pattern:
# threads-{nr_threads}_cores-{cpu_conf}_{iteration}.txt
#
# Each file with cpu usage data should be named with the pattern:
# cpu_usage_threads-{nr_threads}_cores-{cpu_conf}_{iteration}.txt
#
# The results are saved in a folder called "part4_1_extracted_data" (created beforehand)
######

import numpy as np
import pandas as pd

# Read data from raw file
def read_data(filename):
    data = pd.read_csv(filename, header=None, skiprows=1, delimiter=r"\s+")
    return data

def extract_values_from_line_memcache(data_memcache, memcache_line_number):
    p95 = float(data_memcache.iloc[memcache_line_number, 12])  # Extracting p95
    qps = float(data_memcache.iloc[memcache_line_number, 16])  # Extracting QPS
    return (p95, qps)

def get_cpu_usage_in_section(data_cpu, data_memcache, memcache_line_number):
    ts_start = float(data_memcache.iloc[memcache_line_number, 18])
    ts_end = float(data_memcache.iloc[memcache_line_number, 19])

    # Get all the values of the cpu usage between the start and the end of the section. Get their average
    cpu_within_range = data_cpu[(data_cpu["timestamp"] >= ts_start) & (data_cpu["timestamp"] <= ts_end)]
    return cpu_within_range["cpu_usage"].mean()

# Get avg and std of p95 and qps across files of a specific line. Get avg of cpu usage
def calculate_statistics(values_p95, values_qps, values_cpu_usage):
    avg_p95 = np.mean(values_p95)
    std_p95 = np.std(values_p95)
    avg_qps = np.mean(values_qps)
    std_qps = np.std(values_qps)
    avg_cpu = np.mean(values_cpu_usage)
    return (avg_qps, std_qps, avg_p95, std_p95, avg_cpu)

def main():
    threads = ["1", "2"]
    cores = ["0", "0-1"]
    for thread in threads:
        for nr_cores, core_conf in enumerate(cores):
            print(f"Considering {thread} threads and {core_conf} core configuration")

            output_file = open(f"part4_1_extracted_data/threads_{thread}_cores_{nr_cores+1}.txt", "w")
            output_file.write("avg_qps, std_qps, avg_p95, std_p95, avg_cpu\n")
            
            for line_number in range(25):

                # For each line, gather data from the three runs
                values_p95_runs = []
                values_qps_runs = []
                values_cpu_usage_runs = []
                
                for i in range(3):  # Files contain an index the run index
                    filename_memcache = f"part4_1_raw_outputs/threads-{thread}_cores-{core_conf}_{i}.txt"
                    filename_cpu = f"part4_1_raw_outputs/cpu_usage_threads-{thread}_cores-{core_conf}_{i}.txt"
                    
                    data_memcache = read_data(filename_memcache)
                    data_cpu = read_data(filename_cpu)
                    data_cpu.columns = ["timestamp", "cpu_usage"]
                    
                    p95, qps = extract_values_from_line_memcache(data_memcache, line_number)
                    values_p95_runs.append(p95)
                    values_qps_runs.append(qps)

                    cpu_in_section = get_cpu_usage_in_section(data_cpu, data_memcache, line_number)
                    values_cpu_usage_runs.append(cpu_in_section)
            
                avg_qps, std_qps, avg_p95, std_p95, avg_cpu = calculate_statistics(values_p95_runs, values_qps_runs, values_cpu_usage_runs)

                # One decimal place for readibility
                output_file.write(f"{avg_qps:.1f}, {std_qps:.1f}, {avg_p95:.1f}, {std_p95:.1f}, {avg_cpu:.1f}\n")

            output_file.close()

if __name__ == "__main__":
    main()
