####################################
# Extract p95 and timings from the mcperf measurements
####################################

import pandas as pd

for index in range(1, 4):
    data = pd.read_csv(f"part3_raw_outputs/mcperf_{index}.txt", sep='\s+', engine='python')

    required_columns = data[['p95', 'ts_start', 'ts_end']]

    required_columns.to_csv(f"part3_extracted_data/mcperf_stats_{index}.txt", index=False)
