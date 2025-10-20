# file: utils/determinism.py
"""
Deterministic evaluation logic using SHA256 hashing.
"""

import hashlib
import json
import statistics
from datetime import datetime, timezone
from typing import List

from .schema import EvaluationResult, EvaluationConfig, RunResult
from .io import calculate_sha256


def generate_label_from_hash(seed: int, text: str, run_idx: int) -> str:
    """Generate deterministic label (A, B, C) from hash."""
    hash_input = f"{seed}|{text}|{run_idx}"
    hash_value = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    # Convert first 8 chars of hash to int and take mod 3
    hash_int = int(hash_value[:8], 16)
    label_idx = hash_int % 3
    
    # Introduce 10% flip to simulate controlled instability
    flip_hash = int(hash_value[8:16], 16)
    if flip_hash % 10 == 0:  # 10% chance to flip
        label_idx = (label_idx + 1) % 3
    
    return chr(65 + label_idx)  # A, B, or C


def generate_latency_from_hash(seed: int, text: str, run_idx: int) -> int:
    """Generate deterministic latency from hash."""
    hash_input = f"{seed}|{text}|{run_idx}|latency"
    hash_value = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    # Convert hash to int and map to 100-109ms range
    hash_int = int(hash_value[:8], 16)
    latency = 100 + (hash_int % 10)
    
    return latency


def calculate_reproducibility_score(run_results: List[RunResult]) -> float:
    """Calculate reproducibility score (majority label rate)."""
    if not run_results:
        return 0.0
    
    # Count labels
    labels = [result.label for result in run_results]
    label_counts = {}
    for label in labels:
        label_counts[label] = label_counts.get(label, 0) + 1
    
    # Find majority
    max_count = max(label_counts.values())
    total_runs = len(labels)
    
    return max_count / total_runs


def run_deterministic_evaluation(text: str, config: EvaluationConfig) -> EvaluationResult:
    """Run deterministic evaluation and return results."""
    
    # Generate timestamp
    timestamp_utc = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    # Calculate hashes
    input_sha256 = calculate_sha256(text)
    config_str = config.model_dump_json()
    config_sha256 = calculate_sha256(config_str)
    
    # Run evaluations
    run_results = []
    for run_idx in range(config.runs):
        label = generate_label_from_hash(config.seed, text, run_idx)
        latency = generate_latency_from_hash(config.seed, text, run_idx)
        
        run_result = RunResult(
            run_idx=run_idx,
            label=label,
            latency_ms=latency,
            hash_input=f"{config.seed}|{text}|{run_idx}"
        )
        run_results.append(run_result)
    
    # Calculate metrics
    reproducibility_score = calculate_reproducibility_score(run_results)
    latencies = [r.latency_ms for r in run_results]
    latency_mean = statistics.mean(latencies)
    latency_stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
    latency_variance_ratio = latency_stdev / latency_mean if latency_mean > 0 else 0.0
    
    # Determine pass/fail
    reproducibility_passed = reproducibility_score >= config.reproducibility_threshold
    variance_passed = latency_variance_ratio <= config.variance_threshold
    overall_passed = reproducibility_passed and variance_passed
    
    # Create result object
    result = EvaluationResult(
        timestamp_utc=timestamp_utc,
        input_text=text,
        input_sha256=input_sha256,
        config_sha256=config_sha256,
        results_sha256="",  # Will be calculated after JSON serialization
        seed=config.seed,
        runs=config.runs,
        reproducibility_threshold=config.reproducibility_threshold,
        variance_threshold=config.variance_threshold,
        org_name=config.org_name,
        doi=config.doi,
        run_results=run_results,
        reproducibility_score=reproducibility_score,
        latency_mean_ms=latency_mean,
        latency_stdev_ms=latency_stdev,
        latency_variance_ratio=latency_variance_ratio,
        reproducibility_passed=reproducibility_passed,
        variance_passed=variance_passed,
        overall_passed=overall_passed
    )
    
    # Calculate results SHA256 by serializing without the results_sha256 field
    result_dict = result.model_dump()
    result_dict['results_sha256'] = ""  # Clear it for hash calculation
    result_json = json.dumps(result_dict, sort_keys=True, default=str)
    result.results_sha256 = calculate_sha256(result_json)
    
    return result
