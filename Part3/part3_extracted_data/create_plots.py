import pandas as pd
import matplotlib.pyplot as plt

for index in range(1, 4):
    mcperf_stats = pd.read_csv(f"mcperf_stats_{index}.txt")
    pods_times = pd.read_csv(f"time_pods_{index}.txt")

    # Get the time 0 by looking at the time the first job started
    start_time = pods_times['Start'].min()
    end_time = pods_times['Stop'].max()

    print(start_time, end_time)

    # Adjust timings according to the start
    mcperf_stats['ts_start'] = (mcperf_stats['ts_start'] - start_time) * 1e-6
    mcperf_stats['ts_end'] = (mcperf_stats['ts_end'] - start_time) * 1e-6
    print(mcperf_stats['ts_start'])
    pods_times['Start'] = (pods_times['Start'] - start_time) * 1e-6
    pods_times['Stop'] = (pods_times['Stop'] - start_time) * 1e-6

    # Step 2: Plot the bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(mcperf_stats['ts_start'], mcperf_stats['p95'], width=(mcperf_stats['ts_end'] - mcperf_stats['ts_start']), color='blue', alpha=0.7)

    # Set labels and title
    plt.xlabel('Timestamp')
    plt.ylabel('p95')
    plt.title('p95 over time')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Show plot
    plt.tight_layout()
    plt.show()
