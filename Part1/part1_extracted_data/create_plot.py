######
# Still Work In Progress, useful mainly to visualize the data for now
# The input format should be the one created using the script "extract_info_from_logs.py"
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
            
            # avg_qps, avg_p95, std_p95
            data.append([float(values[0]), float(values[1]), float(values[2])])
    return data

# Plot information about interference. Transform ns to ms
def plot_file(filename, marker):
    data = read_data(filename)
    x = [float(row[0]) for row in data]
    y = [float(row[1]/1000) for row in data]  # Transform into ms
    yerr_std = [row[2]/1000 for row in data]

    base_name = os.path.basename(filename)
    main_name = base_name.split('_')[0]

    plt.errorbar(x, y, yerr=yerr_std, capsize=8, label=main_name, linewidth=2.5,
                 marker=marker, markersize=12, markerfacecolor='None', markeredgewidth=2.5)

# Express thousands with K in plot
def thousands_formatter(x, pos):
    return '{:.0f}K'.format(x * 1e-3)

# Main names of the files
interferences = ["none", "cpu", "l1d", "l1i", "l2", "llc", "membw"]
markers = ['o', 'v', '1', 's', 'p', '*', 'X']

# Plotting
plt.figure()
for interference, marker in zip(interferences, markers):
    filename = f"{interference}_interference.txt"
    plot_file(filename, marker)

#### Plot look

## Axis
axis_label_font = {'fontsize': 13, 'fontweight': 'bold'}
plt.xlabel('Queries Per Second (QPS)', fontdict=axis_label_font)
plt.ylabel('95th percentile latency (ms)', fontdict=axis_label_font)

## Title
title_font = {'fontsize': 14, 'fontweight': 'bold'}
plt.title('''
95th Percentile Latency with difference interferences\n
Error bars: Standard deviation (3 repetitions per point)
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
handles, labels = plt.gca().get_legend_handles_labels()
handles = [h[0] for h in handles]  # Remove error bars from legend
plt.gca().legend(handles, labels, fontsize=13)

plt.ylim(0, 8)

plt.show()
