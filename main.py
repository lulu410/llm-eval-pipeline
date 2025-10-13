#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deterministic LLM evaluation demo (policy-aligned).
- Cross-platform CLI (Mac/Linux/Windows)
- Reads config.yaml and examples/input.jsonl
- Produces: data/results/results.json + data/results/run.log
- Deterministic labels & latency via SHA256(seed|prompt|run_idx)
- Metrics: reproducibility (majority-label rate) and latency variance (stdev/mean)
- Provenance: embeds SHA256 of config and input in results.json
"""

import argparse
import json
import os
import sys
import time
import hashlib
import statistics
import yaml
from datetime import datetime
from pathlib import Path


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deterministic_label(seed: int, prompt: str, run_idx: int) -> str:
    """
    Returns a deterministic categorical label in {"A","B","C"}.
    Base label depends on (seed, prompt). With 10% probability per run index,
    it flips to introduce controlled instability (to make reproducibility meaningful).
    """
    base_h = int(sha256_str(f"{seed}|{prompt}"), 16)
    base = "ABC"[base_h % 3]

    flip_h = int(sha256_str(f"{seed}|{prompt}|{run_idx}|flip"), 16)
    if (flip_h % 10) == 0:  # 10% chance to flip
        return "ABC"[((base_h % 3) + 1) % 3]
    return base


def deterministic_latency_ms(seed: int, prompt: str, run_idx: int) -> int:
    """
    Returns a deterministic latency in milliseconds within [100..109],
    derived from SHA256 so it is identical across machines.
    """
    h = int(sha256_str(f"{seed}|{prompt}|{run_idx}|lat"), 16)
    return 100 + (h % 10)


def load_input_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            yield obj["prompt"]


def run_eval(cfg_path: Path):
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    seed = int(cfg["seed"])
    runs = int(cfg["runs"])
    variance_threshold = float(cfg["variance_threshold"])
    reproducibility_threshold = float(cfg["reproducibility_threshold"])
    input_path = Path(cfg["input_path"])
    output_dir = Path(cfg["output_dir"])

    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "run.log"
    results_path = output_dir / "results.json"

    prompts = list(load_input_jsonl(input_path))
    input_sha = file_sha256(input_path)
    config_sha = file_sha256(cfg_path)

    start = time.time()
    with log_path.open("w", encoding="utf-8") as logf:
        ts = datetime.utcnow().isoformat() + "Z"
        logf.write(f"[{ts}] start seed={seed} runs={runs} input={input_path}\n")
        logf.write(f"input_sha256={input_sha}\nconfig_sha256={config_sha}\n")

        latencies = []
        majority_rates = []

        for p in prompts:
            labels = []
            for r in range(runs):
                labels.append(deterministic_label(seed, p, r))
                latencies.append(deterministic_latency_ms(seed, p, r))
            majority = max(set(labels), key=labels.count)
            rate = labels.count(majority) / runs
            majority_rates.append(rate)
            logf.write(f"prompt='{p[:60]}...' majority={majority} rate={rate:.3f}\n")

        mean_ms = statistics.mean(latencies) if latencies else 0.0
        stdev_ms = statistics.pstdev(latencies) if len(latencies) > 1 else 0.0
        var_ratio = (stdev_ms / mean_ms) if mean_ms else 0.0

        repro_score = (sum(majority_rates) / len(majority_rates)) if majority_rates else 0.0

        results = {
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "seed": seed,
            "runs": runs,
            "num_prompts": len(prompts),
            "latency_mean_ms": round(mean_ms, 3),
            "latency_stdev_ms": round(stdev_ms, 3),
            "latency_variance_ratio": round(var_ratio, 4),
            "variance_threshold": variance_threshold,
            "variance_pass": var_ratio < variance_threshold,
            "reproducibility_score": round(repro_score, 3),
            "reproducibility_threshold": reproducibility_threshold,
            "reproducibility_pass": repro_score >= reproducibility_threshold,
            "input_sha256": input_sha,
            "config_sha256": config_sha,
            "system": {
                "python": sys.version.split()[0],
                "platform": sys.platform,
            },
        }

        json.dump(results, results_path.open("w", encoding="utf-8"), indent=2)
        logf.write(
            f"latencies={len(latencies)} mean={mean_ms:.3f} "
            f"stdev={stdev_ms:.3f} ratio={var_ratio:.4f}\n"
        )
        logf.write(f"[done] wrote {results_path}\n")

    print(f"[✓] Wrote results to {results_path}")
    print(f"[i] Log at {log_path}")
    return results_path


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic evaluation pipeline (reproducibility & latency variance)."
    )
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()
    run_eval(Path(args.config))


if __name__ == "__main__":
    main()

