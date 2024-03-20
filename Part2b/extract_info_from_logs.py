######
# Raw logs in folder "part2b_raw_outputs". Each file should be named with the pattern:
# {workload}_{nr_threads}.txt
#
# Necessary to install the library tabulate
######

import re
from tabulate import tabulate
import matplotlib.pyplot as plt

# Search for the time in the file and extract it
def extract_time_from_file(filename):
    with open(filename, 'r') as file:
        for line in file:
            if 'real' in line:
                match = re.search(r'real\s+(\d+)m([\d.]+)s', line)
                if match:
                    minutes = int(match.group(1))
                    seconds = float(match.group(2))
                    return (minutes * 60 + seconds) * 1000
    return None

def main():
    all_workloads = ["blackscholes", "canneal", "dedup", "ferret", "freqmine", "radix", "vips"]
    all_threads_amount = ["1", "2", "4", "8"]

    table = [['Workload'] + all_threads_amount]

    speedup_data = {}

    for workload in all_workloads:
        row = [workload]
        
        one_thread_time = None
        speedup_data[workload] = []
        
        for nr_threads in all_threads_amount:
            filename = f"part2b_raw_outputs/{workload}_{nr_threads}.txt"
            time_ms = extract_time_from_file(filename)
            
            if time_ms is not None:
                if one_thread_time is None:
                    one_thread_time = time_ms
                    
                speedup = one_thread_time / time_ms
                row.append(speedup)
                speedup_data[workload].append(speedup)
            else:
                row.append(None)

        table.append(row)

    print(tabulate(table, headers='firstrow', tablefmt='grid'))

    # Plotting
    plt.figure(figsize=(10, 6))
    for workload, speeds in speedup_data.items():
        plt.plot(all_threads_amount, speeds, marker='o', label=workload)

    plt.xlabel('Number of Threads')
    plt.ylabel('Speedup')
    plt.title('Speedup vs Number of Threads')
    plt.legend()
    plt.grid(True)
    plt.xticks(all_threads_amount)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
