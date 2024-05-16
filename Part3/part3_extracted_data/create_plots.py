####################################
# Create the plot showing the P95 latency of memcached and the scheduling of different jobs
####################################

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe


colors = {
    "parsec-blackscholes": "#CCA000",
    "parsec-canneal": "#CCCCAA",
    "parsec-dedup": "#CCACCA",
    "parsec-ferret": "#AACCCA",
    "parsec-freqmine": "#0CCA00",
    "parsec-radix": "#00CCA0",
    "parsec-vips": "#CC0A00"
    }


workload_labels = {
    "parsec-blackscholes": "Blackscholes - node-a-2core",
    "parsec-canneal": "Canneal - node-b-4core",
    "parsec-dedup": "Dedup - node-b-4core",
    "parsec-ferret": "Ferret - node-b-4core",
    "parsec-freqmine": "Freqmine - node-c-8core",
    "parsec-radix": "Radix - node-c-8core",
    "parsec-vips": "Vips - node-c-8core"
    }


for index in range(1, 4):
    mcperf_stats = pd.read_csv(f"mcperf_stats_{index}.txt")
    pods_times = pd.read_csv(f"time_pods_{index}.txt")

    # Get the time 0 by looking at the time the first job started
    start_time = pods_times['Start'].min()
    end_time = pods_times['Stop'].max()

    relative_start_time = 0
    relative_end_time = (end_time - start_time) * 1e-3

    # Adjust timings making 0 the time the first job starts. Move from ms to s
    mcperf_stats['ts_start'] = (mcperf_stats['ts_start'] - start_time) * 1e-3
    mcperf_stats['ts_end'] = (mcperf_stats['ts_end'] - start_time) * 1e-3

    pods_times['Start'] = (pods_times['Start'] - start_time) * 1e-3
    pods_times['Stop'] = (pods_times['Stop'] - start_time) * 1e-3

    # Plot the bars
    bar_width = mcperf_stats['ts_end'].diff().min()
    plt.bar(mcperf_stats['ts_start'], mcperf_stats['p95'], width=bar_width, color='indigo', alpha=0.15, edgecolor='black', linewidth=1, zorder=0)

    # Add vertical lines for each pair of values in pods_times['Start'] and pods_times['Stop']
    for i, row in pods_times.iterrows():
        workload = row['Workload']
        if(workload == 'memcached'):
            continue
        
        plt.axvline(row['Start'], color=colors[workload], linestyle='-', linewidth=3.5, zorder=1,
                     path_effects=[pe.Stroke(linewidth=4.5, foreground='black'), pe.Normal()], label=workload_labels[workload]+" - Start")  # Thick vertical line
        plt.axvline(row['Stop'], color=colors[workload], linestyle='--', linewidth=3.5, zorder=1,
                     path_effects=[pe.Stroke(linewidth=4.5, foreground='black'), pe.Normal()], label=workload_labels[workload]+" - End")

    #### Plot look

    ## Axis
    axis_label_font = {'fontsize': 13, 'fontweight': 'bold'}
    plt.xlabel('Time (s)', fontdict=axis_label_font)
    plt.ylabel('95th Percentile Latency (us)', fontdict=axis_label_font)

    ## Title
    title_font = {'fontsize': 14, 'fontweight': 'bold'}
    plt.title(f"95th Percentile Latency over Time. Run {index}", fontdict=title_font, linespacing=0.5)

    ## Ticks
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)

    ## Lines
    plt.gca().spines['top'].set_color('gray')
    plt.gca().spines['right'].set_color('gray')
    plt.gca().spines['bottom'].set_color('black')
    plt.gca().spines['left'].set_color('black')

    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')

    ## Legend
    plt.legend()

    plt.xlim(relative_start_time, relative_end_time)

    # Borders work on full screen image
    plt.subplots_adjust(left=0.05, right=0.98, top=0.9, bottom=0.09)
    plt.show()
