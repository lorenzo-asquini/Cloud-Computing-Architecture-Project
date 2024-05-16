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
                # The first time retrieved is the one relative to the case where only one thread is used
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
    markers = ['o', 'v', '1', 's', 'p', '*', 'X']
    for (workload, speedup), marker in zip(speedup_data.items(), markers):

        plt.plot(all_threads_amount, speedup, label=workload, linewidth=2.5,
                 marker=marker, markersize=12, markeredgewidth=2.5)

    #### Plot look

    ## Axis
    axis_label_font = {'fontsize': 13, 'fontweight': 'bold'}
    plt.xlabel('Number of Threads', fontdict=axis_label_font)
    plt.ylabel('Speedup', fontdict=axis_label_font)

    ## Title
    title_font = {'fontsize': 14, 'fontweight': 'bold'}
    plt.title('''
    Speedup vs. Number of Threads for different jobs
    ''', fontdict=title_font)

    ## Ticks
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.xticks(all_threads_amount)

    ## Lines
    plt.gca().spines['top'].set_color('gray')
    plt.gca().spines['right'].set_color('gray')
    plt.gca().spines['bottom'].set_color('black')
    plt.gca().spines['left'].set_color('black')

    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')

    ## Legend
    plt.legend(fontsize=13)

    # Borders work on full screen image
    plt.subplots_adjust(left=0.05, right=0.98, top=0.92, bottom=0.09)
    plt.show()


if __name__ == "__main__":
    main()
