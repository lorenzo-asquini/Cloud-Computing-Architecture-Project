######
# Still Work In Progress, useful mainly to visualize the data for now
# The input format should be the one created using the script "extract_info_from_logs.py"
######

import os
import matplotlib.pyplot as plt

# Read data from file
def read_data(filename):
    data = []
    with open(filename, 'r') as file:
        next(file)  # Skip the header. Used only for human understanding
        for line in file:
            values = line.strip().split(',')
            
            # avg_qps, avg_p95, min_p95, max_p5
            data.append([float(values[0]), float(values[2]), float(values[1]), float(values[3])])
    return data

def plot_file(filename, marker):
    data = read_data(filename)
    x = [float(row[0]) for row in data]
    y = [float(row[1]) for row in data]
    yerr_min = [float(row[1]-row[2]) for row in data]
    yerr_max = [float(row[3]-row[1]) for row in data]

    base_name = os.path.basename(filename)
    main_name = base_name.split('_')[0]

    plt.errorbar(x, y, yerr=[yerr_min, yerr_max], capsize=5, label=main_name, linewidth=2,
                 marker=marker, markersize=8, markerfacecolor='None', markeredgewidth=2)

# Main names of the files
interferences = ["none", "cpu", "l1d", "l1i", "l2", "llc", "membw"]
markers = ['o', 's', '^', 'D', 'x', '*', 'P']

# Plotting
plt.figure()
for interference, marker in zip(interferences, markers):
    filename = f"{interference}_interference.txt"
    plot_file(filename, marker)

plt.xlabel('avg_qps')
plt.ylabel('avg_p95')
plt.title('Interference Data')
plt.legend()
plt.grid(True)


plt.ylim(0, 8000)

plt.show()
