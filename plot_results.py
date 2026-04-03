import matplotlib.pyplot as plt

def extract_times(file):
    times = []
    with open(file) as f:
        for line in f:
            if "Packet received at time:" in line:
                t = float(line.strip().split()[-1])
                times.append(t)
    return times

# 🔹 Load data
baseline = extract_times("baseline_output.txt")
ml = extract_times("ml_output.txt")

# 🔹 Plot
plt.figure()
plt.plot(baseline, label="Baseline (No ML)")
plt.plot(ml, label="ML QoS")

plt.xlabel("Packet Index")
plt.ylabel("Time (seconds)")
plt.title("Latency Comparison: ML vs Baseline")
plt.legend()

plt.grid()
#plt.show()
plt.savefig("latency_comparison.png")
