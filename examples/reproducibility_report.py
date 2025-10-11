import json, random, statistics, time, os
from datetime import datetime

os.makedirs("data/results", exist_ok=True)

def simulate_latency(num_runs=10):
    return [random.uniform(0.8, 1.2) * 100 for _ in range(num_runs)]

def evaluate_reproducibility(runs):
    mean = statistics.mean(runs)
    stdev = statistics.stdev(runs)
    variance = stdev / mean
    pass_fail = variance < 0.05
    return {
        "latency_mean_ms": round(mean, 2),
        "latency_stdev_ms": round(stdev, 2),
        "latency_variance_ratio": round(variance, 4),
        "reproducibility_pass": pass_fail,
    }

if __name__ == "__main__":
    start = time.time()
    runs = simulate_latency()
    metrics = evaluate_reproducibility(runs)
    metrics["timestamp"] = datetime.utcnow().isoformat()
    metrics["runs"] = runs
    metrics["runtime_sec"] = round(time.time() - start, 3)

    out_path = "data/results/example_summary.json"
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[✓] Saved reproducibility metrics to {out_path}")

