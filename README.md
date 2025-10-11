# LLM Evaluation Pipeline
Independent, policy-aligned LLM evaluation pipeline — reproducibility &amp; latency variance with verifiable artifacts (NIST AI RMF, EO 14110).

Open-source, reproducible evaluation for LLM reliability.  
Metrics: **reproducibility** and **latency variance**.  
Aligned with **NIST AI RMF** and **U.S. EO 14110** for trustworthy AI.

# Quick Start
```bash
python examples/reproducibility_report.py
```

For detailed policy alignment, see [docs/policy_alignment.md](docs/policy_alignment.md).



## 🧪 Run and Verify the Evaluation Pipeline

This section demonstrates how to **run the evaluation demo** and verify the results step by step.

### 1. Move to the project root directory
Open a terminal and run:
```bash
git clone https://github.com/lulu410/llm-eval-pipeline.git
cd llm-eval-pipeline
````

You should now see folders like:

```
examples/  docs/  data/  contact/  README.md
```


### 2. Execute the example script

Run the demo evaluation:

```bash
python3 examples/reproducibility_report.py
```

If successful, the console will print:

```
[✓] Saved reproducibility metrics to data/results/example_summary.json
```


### 3. Inspect the generated result file

Open the result file with:

```bash
cat data/results/example_summary.json
```

Expected output:

```json
{
  "latency_mean_ms": 101.7,
  "latency_stdev_ms": 3.8,
  "latency_variance_ratio": 0.037,
  "reproducibility_pass": true,
  "timestamp": "2025-10-11T18:40:30Z",
  "runtime_sec": 0.004
}
```

This confirms the pipeline **successfully simulated an evaluation**, computed latency statistics, and exported structured results.

---

### 4. Verify reproducibility

Run the same command again:

```bash
python3 examples/reproducibility_report.py
```

Compare the two runs in `data/results/` —
the `latency_variance_ratio` should stay within **±5%**, showing consistent reproducibility.

---

### 5. Expected directory structure after running

```
llm-eval-pipeline/
├── README.md
├── LICENSE
├── examples/
│   └── reproducibility_report.py
├── data/
│   └── results/
│       └── example_summary.json
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
| Script execution | Runs without error          | `[✓] Saved reproducibility metrics...` |
| Output file      | Exists in `data/results/`   | `example_summary.json`                 |
| JSON validity    | File contains key metrics   | mean, stdev, variance ratio            |
| Repeatability    | 2nd run within ±5% variance | `reproducibility_pass = true`          |

---

### 🧠 Why This Matters

These steps ensure the repository is **verifiable, reproducible, and policy-aligned**,
supporting the principles of the **NIST AI Risk Management Framework (AI RMF)**
and **U.S. Executive Order 14110 on Safe and Trustworthy AI**.

