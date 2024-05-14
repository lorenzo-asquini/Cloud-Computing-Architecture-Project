from datetime import datetime, timedelta

def start_end_epoch_scheduler(log_file):
    epoch_times = []

    with open(log_file, 'r') as file:
        for line in file:
            if line.strip() != "":
                timestamp = line.strip().split()[0]
                datetime_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
                epoch_time = int(datetime_obj.timestamp()) + 2 * 3600 # Adjust time zone
                epoch_times.append(epoch_time * 1000) # To ms

    return epoch_times

def parse_memcache_start_timestamp(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("Timestamp start:"):
                start_timestamp = int(line.split(":")[1].strip())
                return start_timestamp

def process_read_lines(file_path, start_timestamp_ms):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("read"):
                start_timestamp_ms += 3000  # Increase by 10 seconds for each line
                line_parts = line.strip().split()
                p95_value = float(line_parts[12])  # Assuming p95 is always 7th from the end
                data.append((start_timestamp_ms, p95_value))
    return data

log_file = 'log4.txt'
epoch_times = start_end_epoch_scheduler(log_file)
memcache_log_file = "mlog4.txt"
start_timestamp_ms = parse_memcache_start_timestamp(memcache_log_file)
data = process_read_lines(memcache_log_file, start_timestamp_ms)

tot_points = 0
slo = 0
for time, value in data:
    if time-3000 > epoch_times[0] and time+3000 < epoch_times[-1]:
        if(value > 1000):
            print(time, value)
            slo += 1

        tot_points += 1
print(epoch_times[0], epoch_times[-1])
print(tot_points, slo, 100*slo/tot_points)
