# LLM Evaluation Pipeline
Independent, policy-aligned LLM evaluation pipeline — reproducibility &amp; latency variance with verifiable artifacts (NIST AI RMF, EO 14110).

Open-source pipeline for **reliable, reproducible** LLM evaluation with deterministic metrics and audit-friendly artifacts.

- **Deterministic:** Results depend only on `config.yaml` + `examples/input.jsonl` (no external APIs).
- **Reproducibility metrics:** Majority-label consistency across repeated runs.
- **Latency variance:** Stability via stdev/mean ratio.
- **Provenance:** SHA256 fingerprints for input/config; structured logs for audit.
- **Policy alignment:** NIST AI RMF (Govern/Map/Measure/Manage) & U.S. EO 14110.

# Quick Start
For detailed policy alignment, see [docs/policy_alignment.md](docs/policy_alignment.md).

## 🧪 Run and Verify the Evaluation Pipeline

This section demonstrates how to **run the evaluation demo** and verify the results step by step.

### 1. Move to the project root directory
Open a terminal and run:
```bash
git clone https://github.com/lulu410/llm-eval-pipeline.git
cd llm-eval-pipeline
````


### 2. Execute the example script

Run the evaluation:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py --config config.yaml
```

If successful, the console will print:

```
[✓] Wrote results to data/results/results.json
[i] Log at data/results/run.log
```


### 3. Inspect the generated result file

Open the result file with:

```bash
cat data/results/results.json
```

Expected output:

```json
{
  "timestamp_utc": "2025-10-13T12:00:00Z",
  "seed": 20251012,
  "runs": 10,
  "num_prompts": 3,
  "latency_mean_ms": 104.9,
  "latency_stdev_ms": 2.725,
  "latency_variance_ratio": 0.026,
  "variance_threshold": 0.05,
  "variance_pass": true,
  "reproducibility_score": 0.933,
  "reproducibility_threshold": 0.9,
  "reproducibility_pass": true,
  "input_sha256": "55f0fd8f8ab49ea8ef68b7cbfd1d269b994ac518d5f8833dbcd79600105d033d",
  "config_sha256": "5df99603ac9d594b68d2e681831132ea4a6b9a397bd8424126849b5d2ac1a6f1",
  "system": { "python": "3.11.9", "platform": "darwin" }
}
```

This confirms the pipeline **successfully simulated an evaluation**, computed latency statistics, and exported structured results.

---

### 4. Reproducibility

- Deterministic generation: labels & latencies are derived from `SHA256(seed|prompt|run_idx)` — no external APIs.

- Provenance embedded: `input_sha256` and `config_sha256` are written into `results.json`.

- Single-source config: changing `config.yaml` is the only way to change outcomes.

---

### 5. Expected directory structure after running

```
llm-eval-pipeline/
├── README.md
├── LICENSE
├── config.yaml
├── main.py
├── requirements.txt
├── examples/
│   ├── input.jsonl
│   └── reproducibility_report.py
├── data/
│   └── results/
│       ├── example_summary.json
│       ├── results.json
│       └── run.log
├── docs/
│   └── policy_alignment.md
└── contact/
    └── contact.md
```


### 6. Clean and rerun (optional)

If you want to restart the test:

```bash
rm -rf data/results
mkdir -p data/results
python3 examples/reproducibility_report.py
```


### ✅ Verification Summary

| Step             | What to Check               | Expected Result                        |
| ---------------- | --------------------------- | -------------------------------------- |
| Script execution | Runs without error          | `[✓] Wrote results to data/results/...` |
| Output file      | Exists in `data/results/`   | `example_summary.json`                 |
| JSON validity    | File contains key metrics   | mean, stdev, variance ratio            |
| Repeatability    | 2nd run within ±5% variance | `reproducibility_pass = true`          |

---

### Policy reference
Designed in line with **U.S. Executive Order 14110** and the **NIST AI Risk Management Framework (AI RMF 1.0)**:
- Govern — transparent configs, artifact fingerprints, audit logs
- Map — explicit evaluation context (seed, runs, input set)
- Measure — reproducibility & latency variance with thresholds
- Manage — repeatable runs for drift checks and CI quality gates