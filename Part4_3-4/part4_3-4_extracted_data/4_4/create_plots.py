####################################
# Plot A: QPS, P95 latency and job scheduling over time
# Plot B: QPS, cores assigned to memcached and job scheduling over time
# The data must be located in "part4_3-4_raw_outputs"
####################################

import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.ticker import FuncFormatter


# Colors required by the report rulers
colors = {
    "blackscholes": "#CCA000",
    "canneal": "#CCCCAA",
    "dedup": "#CCACCA",
    "ferret": "#AACCCA",
    "freqmine": "#0CCA00",
    "radix": "#00CCA0",
    "vips": "#CC0A00"
    }


# Used to have capitalized first letters
job_names = {
    "blackscholes": "Blackscholes",
    "canneal": "Canneal",
    "dedup": "Dedup",
    "ferret": "Ferret",
    "freqmine": "Freqmine",
    "radix": "Radix",
    "vips": "Vips"
    }


# Extract data from the memcache measure log
def extract_measure_memcache_data(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Extract start timestamps
    for line in lines:
        if line.startswith("Timestamp start:"):
            start_timestamp = int(line.split(":")[1].strip())
            break

    # Extract p95 values and QPS values for lines starting with "read"
    data = {"timestamp": [], "p95": [], "qps": []}

    read_line_idx = 0  # Skip lines without useful data
    for line in lines:
        if line.startswith("read"):
            tokens = line.split()

            # Each data point is separated with 10 seconds from the previous one
            data["timestamp"].append(start_timestamp + read_line_idx * 3000)
            data["p95"].append(float(tokens[12]))
            data["qps"].append(float(tokens[16]))
            read_line_idx += 1

    return data


# The job logger keeps track of time with datetime dates.
# Adjust the timezone and take the time with ms accuracy
def epoch_ms_from_datetime(datetime_line):
    datetime_str = datetime_line.strip().split()[0]
    datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
    epoch_time = int((datetime_obj.timestamp() + 7200) * 1000)  # Adjust time zone. From s to ms
    return epoch_time


# Extract data from the jobs log
def extract_jobs_data(file_path):
    # Jobs ordered as they were executed
    jobs = ["radix", "blackscholes", "ferret", "freqmine", "canneal", "dedup", "vips"]

    # For each job, record start, end, pause and unpause epoch times in ms
    job_times = {job: {} for job in jobs}
    
    for job in jobs:

        # Create arrays to store pause and unpause times
        job_times[job]["pause"] = []
        job_times[job]["unpause"] = []
            
        with open(file_path, 'r') as file:
            
            for line in file:
                # Only one start or end
                if f" start {job}" in line:
                    job_times[job]["start"] = epoch_ms_from_datetime( line.strip().split()[0] )

                if f" end {job}" in line:
                    job_times[job]["end"] = epoch_ms_from_datetime( line.strip().split()[0] )

                # Possibly multiple pause and unpause. The number of pause and unpause is equal
                if f" pause {job}" in line:
                    job_times[job]["pause"].append(epoch_ms_from_datetime( line.strip().split()[0]) )

                if f" unpause {job}" in line:
                    job_times[job]["unpause"].append(epoch_ms_from_datetime( line.strip().split()[0]) )

    # Get the change of cores of memcache
    memcache_cores = {"timestamp": [], "cores": []}

    with open(file_path, 'r') as file:

        for line in file:
            # At the start, always two cores
            if " start memcached" in line:
                memcache_cores["timestamp"].append(epoch_ms_from_datetime( line.strip().split()[0]) )
                memcache_cores["cores"].append(2)

            if " update_cores memcached" in line:
                memcache_cores["timestamp"].append(epoch_ms_from_datetime( line.strip().split()[0]) )
                
                if " [0]" in line:
                    memcache_cores["cores"].append(1)
                else:
                    memcache_cores["cores"].append(2)

            # At the end always two cores
            if " end scheduler" in line:
                memcache_cores["timestamp"].append(epoch_ms_from_datetime( line.strip().split()[0]) )
                memcache_cores["cores"].append(2)

    return job_times, memcache_cores

# Express thousands with K in plot
def thousands_formatter(x, pos):
    return '{:.0f}K'.format(x * 1e-3)

def plot(file_idx):
   
    memcache_data = extract_measure_memcache_data(f"../../part4_3-4_raw_outputs/4_4_3s/mcperf_{file_idx}.txt")
    job_times, memcache_cores = extract_jobs_data(f"../../part4_3-4_raw_outputs/4_4_3s/jobs_{file_idx}.txt")

    # Get the range of times where there are jobs running
    first_job_start = 12345678901234567890 # Large number just to be able to use min
    last_job_end = 0
    for job in job_times:
        first_job_start = min(first_job_start, job_times[job]["start"])
        last_job_end = max(last_job_end, job_times[job]["end"])

    # Adjust all timings considering when the first job started and transform to seconds

    ## memcache
    for idx in range(len(memcache_data["timestamp"])):
        memcache_data["timestamp"][idx] = (memcache_data["timestamp"][idx] - first_job_start) / 1000

    ## jobs
    for job in job_times:
        job_times[job]["start"] = (job_times[job]["start"] - first_job_start) / 1000
        job_times[job]["end"] = (job_times[job]["end"] - first_job_start) / 1000

        # There is an unpause for each pause
        for idx in range(len(job_times[job]["pause"])):
            job_times[job]["pause"][idx] = (job_times[job]["pause"][idx] - first_job_start) / 1000  
            job_times[job]["unpause"][idx] = (job_times[job]["unpause"][idx] - first_job_start) / 1000

    ## memcache cores
    for idx in range(len(memcache_cores["timestamp"])):
        memcache_cores["timestamp"][idx] = (memcache_cores["timestamp"][idx] - first_job_start) / 1000

    last_job_end = (last_job_end - first_job_start) / 1000
    first_job_start = 0

    # Plotting
    fig, ax1 = plt.subplots()

    # Plot the job execution time as horizontal bars that are placed behind the lines of QPS and p95
    for job in job_times:

        # If there are no pauses, plot a single horizontal bar
        if(len(job_times[job]["pause"]) == 0):
            ax1.barh(job, job_times[job]['end']-job_times[job]['start'], color=colors[job], 
                     left=job_times[job]['start'], label=job_names[job], edgecolor='black')
        
        else:
            # Plot from start to the first pause. Label only in the first
            ax1.barh(job, job_times[job]['pause'][0]-job_times[job]['start'], color=colors[job], 
                     left=job_times[job]['start'], label=job_names[job], edgecolor='black')

            # Plot all intermediate sections between unpauses and pauses
            for idx in range(len(job_times[job]["unpause"])-1):
                ax1.barh(job, job_times[job]['pause'][idx+1]-job_times[job]['unpause'][idx], color=colors[job], 
                         left=job_times[job]['unpause'][idx], edgecolor='black')

            # Plot from the last unpause to the end
            ax1.barh(job, job_times[job]['end']-job_times[job]['unpause'][-1], color=colors[job], 
                     left=job_times[job]['unpause'][-1], edgecolor='black')

    # Remove the labels on the axis for the horizontal bars
    ax1.set_yticks([])
    ax1.set_ylabel('')

    # Plot QPS on the right
    ax2 = ax1.twinx() 
    ax2.plot(memcache_data["timestamp"], memcache_data["p95"], linewidth=2.5, color="tab:blue", label="P95 Latency")

    # Plot p95 on the left
    ax3 = ax2.twinx() 
    ax3.plot(memcache_data["timestamp"], memcache_data["qps"], linewidth=2.5, color="tab:red", label="QPS")
    
    #### Plot look

    ## Axis
    axis_label_font = {'fontsize': 13, 'fontweight': 'bold'}
    ax1.set_xlabel('Time (s)', fontdict=axis_label_font)
    ax1.set_ylabel('95th Percentile Latency (us)', fontdict=axis_label_font, labelpad=45)
    ax3.set_ylabel('QPS', fontdict=axis_label_font)   

    formatter = FuncFormatter(thousands_formatter)
    ax3.yaxis.set_major_formatter(formatter)

    ## Title
    title_font = {'fontsize': 16, 'fontweight': 'bold'}
    plt.title(f"{file_idx}A", fontdict=title_font, linespacing=0.5)

    ## Ticks
    ax1.tick_params(labelsize=14)
    ax2.tick_params(labelsize=14)
    ax3.tick_params(labelsize=14)

    ## Lines
    plt.gca().spines['top'].set_color('gray')
    plt.gca().spines['right'].set_color('gray')
    plt.gca().spines['bottom'].set_color('black')
    plt.gca().spines['left'].set_color('black')

    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')

    ## Legend
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax3.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc='lower right', fontsize=13)

    plt.xlim(first_job_start, last_job_end)

    # Borders work on full screen image
    plt.subplots_adjust(left=0.06, right=0.92, top=0.95, bottom=0.09)
 
    plt.show()

    # Plotting
    fig, ax1 = plt.subplots()

    # Plot the job execution time as horizontal bars that are placed behind the lines of QPS and p95
    for job in job_times:

        # If there are no pauses, plot a single horizontal bar
        if(len(job_times[job]["pause"]) == 0):
            ax1.barh(job, job_times[job]['end']-job_times[job]['start'], color=colors[job], 
                     left=job_times[job]['start'], label=job_names[job], edgecolor='black')
        
        else:
            # Plot from start to the first pause. Label only in the first
            ax1.barh(job, job_times[job]['pause'][0]-job_times[job]['start'], color=colors[job], 
                     left=job_times[job]['start'], label=job_names[job], edgecolor='black')

            # Plot all intermediate sections between unpauses and pauses
            for idx in range(len(job_times[job]["unpause"])-1):
                ax1.barh(job, job_times[job]['pause'][idx+1]-job_times[job]['unpause'][idx], color=colors[job], 
                         left=job_times[job]['unpause'][idx], edgecolor='black')

            # Plot from the last unpause to the end
            ax1.barh(job, job_times[job]['end']-job_times[job]['unpause'][-1], color=colors[job], 
                     left=job_times[job]['unpause'][-1], edgecolor='black')

    # Remove the labels on the axis for the horizontal bars
    ax1.set_yticks([])
    ax1.set_ylabel('')

    # Plot QPS on the right
    ax2 = ax1.twinx() 
    ax2.step(memcache_cores["timestamp"], memcache_cores["cores"], where="post", linewidth=2.5, color="tab:blue", label="Memcached Cores")

    # Plot p95 on the left
    ax3 = ax2.twinx() 
    ax3.plot(memcache_data["timestamp"], memcache_data["qps"], linewidth=2.5, color="tab:red", label="QPS")
    
    #### Plot look

    ## Axis
    axis_label_font = {'fontsize': 13, 'fontweight': 'bold'}
    ax1.set_xlabel('Time (s)', fontdict=axis_label_font)
    ax1.set_ylabel('Cores assigned to memcached', fontdict=axis_label_font, labelpad=30)
    ax3.set_ylabel('QPS', fontdict=axis_label_font)

    formatter = FuncFormatter(thousands_formatter)
    ax3.yaxis.set_major_formatter(formatter)

    ax2.set_yticks([1, 2])

    ## Title
    title_font = {'fontsize': 16, 'fontweight': 'bold'}
    plt.title(f"{file_idx}B", fontdict=title_font, linespacing=0.5)

    ## Ticks
    ax1.tick_params(labelsize=14)
    ax2.tick_params(labelsize=14)
    ax3.tick_params(labelsize=14)

    ## Lines
    plt.gca().spines['top'].set_color('gray')
    plt.gca().spines['right'].set_color('gray')
    plt.gca().spines['bottom'].set_color('black')
    plt.gca().spines['left'].set_color('black')

    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')

    ## Legend
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax3.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc='lower right', fontsize=13)

    plt.xlim(first_job_start, last_job_end)

    # Borders work on full screen image
    plt.subplots_adjust(left=0.06, right=0.92, top=0.95, bottom=0.09)
 
    plt.show()


if __name__ == "__main__":
    for file_idx in range(1, 4):
        plot(file_idx)
