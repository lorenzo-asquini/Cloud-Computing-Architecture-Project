####################################
# Calculate the SLO violation while the different jobs were running
# The data must be located in "part4_3-4_raw_outputs"
####################################

from datetime import datetime

# The job logger keeps track of time with datetime dates.
# Adjust the timezone and take the time with ms accuracy
def epoch_ms_from_datetime(datetime_line):
    datetime_str = datetime_line.strip().split()[0]
    datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
    epoch_time = int((datetime_obj.timestamp() + 7200) * 1000)  # Adjust time zone. From s to ms
    return epoch_time

# Find the timestamps of start and end of the scheduler
def start_end_epoch_scheduler(log_file):

    with open(log_file, 'r') as file:
        for line in file:
            if "start scheduler" in line:
                start_epoch = epoch_ms_from_datetime( line.strip().split()[0] )
            if "end scheduler" in line:
                end_epoch = epoch_ms_from_datetime( line.strip().split()[0] )

    return start_epoch, end_epoch

# Register when SLO was not respected
def process_read_lines(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Extract start timestamps
    for line in lines:
        if line.startswith("Timestamp start:"):
            start_timestamp = int(line.split(":")[1].strip())
            break

    latency_data = []

    nr_datapoints = 0  # Skip lines without useful data
    for line in lines:
        if line.startswith("read"):
            tokens = line.split()
            timestamp = start_timestamp + nr_datapoints * 5000
            p95_latency = float(tokens[12])

            latency_data.append((timestamp, p95_latency))

            nr_datapoints += 1

    return latency_data

for file_idx in range(1, 4):
    memcache_log_file = f"mcperf_testing_5s.txt"
    log_file = f"jobs_testing_5s.txt"

    scheduler_start, scheduler_end = start_end_epoch_scheduler(log_file)
    latency_data = process_read_lines(memcache_log_file)

    slo_violations = 0
    nr_datapoints = 0
    for time, latency in latency_data:
        # Consider also the case where the scheduler starts in the middle of a measure section
        if time > scheduler_start-5000 and time < scheduler_end+5000:
            if latency > 1000:
                slo_violations += 1
            nr_datapoints += 1

    print(f"Nr datapoints: {nr_datapoints}, SLO violations: {slo_violations}, Percentage of violations: {100 * slo_violations / nr_datapoints:.2f}%")
