######
# Raw logs in folder "part2a_raw_outputs". Each file should be named with the pattern:
# {workload}_{interference}.txt
#
# Necessary to install the library tabulate
######

import re
from tabulate import tabulate

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
    all_interferences = ["none", "cpu", "l1d", "l1i", "l2", "llc", "memBW"]

    table = [['Workload'] + all_interferences]

    for workload in all_workloads:
        row = [workload]
        
        none_interference_time = None
        
        for interference in all_interferences:
            filename = f"part2a_raw_outputs/{workload}_{interference}.txt"
            time_ms = extract_time_from_file(filename)
            
            if time_ms is not None:
                if none_interference_time is None:
                    none_interference_time = time_ms
                    
                slowdown = time_ms / none_interference_time
                row.append(slowdown)
            else:
                row.append(None)

        table.append(row)

    print(tabulate(table, headers='firstrow', tablefmt='grid'))

if __name__ == "__main__":
    main()
