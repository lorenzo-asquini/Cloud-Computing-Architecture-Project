######
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
            
            # avg_qps, std_qps, avg_p95, std_p95
            data.append([float(values[0]), float(values[1]), float(values[2]), float(values[3])])
    return data

# Plot information about different thread-cores configurations
def plot_file(filename, marker):
    data = read_data(filename)
    x = [row[0] for row in data]
    xerr_std = [row[1] for row in data]
    y = [row[2] for row in data]  # Times in us
    yerr_std = [row[3] for row in data] 

    name_components = os.path.basename(filename).split('_')
    main_name = f"Threads: {name_components[1][0]}. Cores: {name_components[3][0]}"
    
    plt.errorbar(x, y, xerr=xerr_std, yerr=yerr_std, capsize=8, label=main_name, linewidth=2.5,
                 marker=marker, markersize=8, markerfacecolor='None', markeredgewidth=2.5)

# Express thousands with K in plot
def thousands_formatter(x, pos):
    return '{:.0f}K'.format(x * 1e-3)

# Main names of the files
configurations = [(1,1), (1,2), (2,1), (2,2)]  #(threads, cores)
markers = ['o', 'v', '1', 's']

# Plotting
plt.figure()
for conf, marker in zip(configurations, markers):
    filename = f"threads_{conf[0]}_cores_{conf[1]}.txt"
    plot_file(filename, marker)

#### Plot look

## Axis
axis_label_font = {'fontsize': 13, 'fontweight': 'bold'}
plt.xlabel('Queries Per Second (QPS)', fontdict=axis_label_font)
plt.ylabel('95th Percentile Latency (us)', fontdict=axis_label_font)

## Title
title_font = {'fontsize': 14, 'fontweight': 'bold'}
plt.title('''
95th Percentile Latency with Different Threads-Cores Configurations\n
Error Bars: Standard Deviation (3 repetitions per point)
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

plt.ylim(0, 2250)
plt.xlim(0, 125000)

# Borders work on full screen image
plt.subplots_adjust(left=0.07, right=0.98, top=0.9, bottom=0.09)
plt.show()
