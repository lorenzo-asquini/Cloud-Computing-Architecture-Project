######
# The input format should be the one created using the script "info_from_logs.py"
######

import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Read data from file
def read_data(filename):
    data = []
    with open(filename, 'r') as file:
        next(file)  # Skip the header. Used only for human understanding
        for line in file:
            values = line.strip().split(',')
            
            # avg_qps, avg_p95, avg_cpu
            data.append([float(values[0]), float(values[2]), float(values[4])])
    return data

# Express thousands with K in plot
def thousands_formatter(x, pos):
    return '{:.0f}K'.format(x * 1e-3)

# Main names of the files
cores = [1, 2]
markers = ['o', 'x']  # One line for p95 latency and one line for cpu usage

# Plotting
plt.figure()
for nr_cores in cores:
    filename = f"threads_2_cores_{nr_cores}.txt"

    #### Plot data

    data = read_data(filename)

    x = [point[0] for point in data]  #QPS
    left_y = [point[1] for point in data]  #p95
    right_y = [point[2] for point in data]  #avg_cpu

    fig, ax1 = plt.subplots()

    # p95
    ax1.plot(x, left_y, linewidth=2.5, marker = markers[0], markersize=8, markerfacecolor='None', markeredgewidth=2.5, color="blue", label="Latency")
    ax1.axhline(y=1000, color='green', linestyle='--', linewidth=2.5, label="Latency: 1ms")

    # Avg CPU
    ax2 = ax1.twinx()
    ax2.plot(x, right_y, linewidth=2.5, marker = markers[1], markersize=8, markerfacecolor='None', markeredgewidth=2.5, color="red", label=f"CPU usage ({nr_cores} cores)")

    #### Plot look

    ## Axis
    axis_label_font = {'fontsize': 13, 'fontweight': 'bold'}
    ax1.set_xlabel('Queries Per Second (QPS)', fontdict=axis_label_font)
    ax1.set_ylabel('95th Percentile Latency (us)', fontdict=axis_label_font)
    ax2.set_ylabel('Average CPU usage (%)', fontdict=axis_label_font)

    ## Title
    title_font = {'fontsize': 14, 'fontweight': 'bold'}
    plt.title('''
    95th Percentile Latency and Average CPU usage\n
    (3 repetitions per point)
    ''', fontdict=title_font, linespacing=0.5)

    ## Ticks
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)

    formatter = FuncFormatter(thousands_formatter)
    plt.gca().xaxis.set_major_formatter(formatter)

    ## Lines
    plt.gca().spines['top'].set_color('gray')
    plt.gca().spines['right'].set_color('gray')
    plt.gca().spines['bottom'].set_color('black')
    plt.gca().spines['left'].set_color('black')

    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')

    ## Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=13)

    ax1.set_xlim(0, 125000)
    ax1.set_ylim(0, 2250)
    ax2.set_ylim(0, 100 * nr_cores)

    # Borders work on full screen image
    plt.subplots_adjust(left=0.07, right=0.94, top=0.9, bottom=0.09)
    fig.show()
