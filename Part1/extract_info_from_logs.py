######
# Raw logs in folder "Raw". Each file should be named with the pattern:
# {inteference}_{runIndex}.txt
#
# The results are saved in a folder called "Extracted" (created beforehand)
######

import numpy as np
import pandas as pd

# Read data from raw file
def read_data(filename):
    data = pd.read_csv(filename, header=None, skiprows=1, delim_whitespace=True)
    return data

def extract_values_from_line(data, line_number):
    p95 = float(data.iloc[line_number, 12])  # Extracting p95
    qps = float(data.iloc[line_number, 16])  # Extracting QPS
    return (p95, qps)

# Get min, max and avg of p95 across files of a specific line. Same thing with avg qps
def calculate_statistics(values_p95, values_qps):
    avg_p95 = np.mean(values_p95)
    avg_qps = np.mean(values_qps)
    min_p95 = np.min(values_p95)
    max_p95 = np.max(values_p95)
    return (min_p95, avg_p95, max_p95, avg_qps)

def main():
    interferences = ["none", "cpu", "l1d", "l1i", "l2", "llc", "membw"]
    for interference in interferences:
        print(f"Considering interference {interference}")

        output_file = open(f"Extracted/{interference}_interference.txt", "w")
        output_file.write("avg_qps, min_p95, avg_p95, max_p95\n")
        
        for line_number in range(11):

            # For each line, gather data from the three runs
            values_p95_runs = []
            values_qps_runs = []
            
            for i in range(3):  # Files contain an index the run index
                filename = f"Raw/{interference}_{i}.txt"
                data = read_data(filename)
                
                p95, qps = extract_values_from_line(data, line_number)
                values_p95_runs.append(p95)
                values_qps_runs.append(qps)
        
            min_p95, avg_p95, max_p95, avg_qps = calculate_statistics(values_p95_runs, values_qps_runs)

            # One decimal place for readibility
            output_file.write(f"{avg_qps:.1f}, {min_p95:.1f}, {avg_p95:.1f}, {max_p95:.1f}\n")

        output_file.close()

if __name__ == "__main__":
    main()
