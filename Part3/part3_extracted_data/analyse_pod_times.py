####################################
# Get average execution time and standard deviation for the different jobs
####################################

import pandas as pd
from tabulate import tabulate

def calculate_stats(file_paths):
    df_list = []

    for file_path in file_paths:
        data = pd.read_csv(file_path, names=['Workload', 'Execution Time', 'Start', 'Stop'], skiprows=1)
        df_list.append(data)

    df = pd.concat(df_list, ignore_index=True)

    # Group by 'Workload' and calculate the mean and standard deviation of 'Execution Time' for each group
    stats = df.groupby('Workload')['Execution Time'].agg(['mean', 'std']).reset_index()

    stats['mean'] = stats['mean'].apply(lambda x: f"{x:.2f}")
    stats['std'] = stats['std'].apply(lambda x: f"{x:.2f}")
    
    return stats


def main():
    file_paths = [f"time_pods_{i}.txt" for i in range(1, 4)]
    stats = calculate_stats(file_paths)

    print(tabulate(stats[['Workload', 'mean', 'std']], headers=["Workload", "Average (s)", "Std (s)"], tablefmt="grid"))


if __name__ == "__main__":
    main()
