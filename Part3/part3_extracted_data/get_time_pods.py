####################################
# Extract times in seconds and timestamps from the json log of the pods
####################################

import json
import sys
from datetime import datetime

time_format = '%Y-%m-%dT%H:%M:%SZ'
for index in range(1, 4):
    file = open(f"../part3_raw_outputs/pods_{index}.json", 'r')
    json_file = json.load(file)

    output_file = open(f"time_pods_{index}.txt", 'w')
    output_file.write("Workload,Execution Time,Start,Stop\n")

    start_times = []
    completion_times = []
    for item in json_file['items']:
        
        name = item['status']['containerStatuses'][0]['name']
        output_file.write(f"{name}, ")
        
        if str(name) != "memcached":
            
            try:
                start_time = float(datetime.strptime(
                        item['status']['containerStatuses'][0]['state']['terminated']['startedAt'],
                        time_format).strftime('%s.%f')) + 7200  # Fix for time zone
                
                completion_time = float(datetime.strptime(
                        item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'],
                        time_format).strftime('%s.%f')) + 7200  # Fix for time zone
                
                output_file.write(f"{completion_time - start_time},{start_time*1000},{completion_time*1000}\n")  # Start and End in ms
                start_times.append(start_time)
                completion_times.append(completion_time)
                
            except KeyError:
                print("Job {0} has not completed....".format(name))
                sys.exit(0)

    if len(start_times) != 7 and len(completion_times) != 7:
        print("You haven't run all the PARSEC jobs. Exiting...")
        sys.exit(0)

    output_file.write(f"{max(completion_times) - min(start_times)},{min(start_times)*1000},{max(completion_times)*1000}\n")  # Start and End in ms
    file.close()
