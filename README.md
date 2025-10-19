# LLM Evaluation Pipeline
Independent, policy-aligned LLM evaluation pipeline — reproducibility &amp; latency variance with verifiable artifacts (NIST AI RMF, EO 14110).
[![DOI](https://zenodo.org/badge/1074443594.svg)](https://doi.org/10.5281/zenodo.17344626)


Enhanced open-source pipeline for **reliable, reproducible** LLM evaluation with advanced features:


## 🏗️ Core Features
- **Deterministic:** Results depend only on `config.yaml` + `examples/input.jsonl` (no external APIs).
- **Reproducibility metrics:** Majority-label consistency across repeated runs.
- **Latency variance:** Stability via stdev/mean ratio.
- **Provenance:** SHA256 fingerprints for input/config; structured logs for audit.
- **Policy alignment:** NIST AI RMF (Govern/Map/Measure/Manage) & U.S. EO 14110.

# Quick Start
For detailed policy alignment, see [docs/policy_alignment.md](docs/policy_alignment.md).

## 🚀 Quick Start Options

### Option 1: Enhanced Multimodal Pipeline (New)

Run the enhanced pipeline with web interface and multimodal support:

```bash
# Install enhanced dependencies
pip install -r requirements.txt

# Run multimodal evaluation demo
python enhanced_main.py demo

# Start web server with UI and API
python enhanced_main.py serve --host 0.0.0.0 --port 8000
```

**Setup for AI Models (Optional):**
```bash
# Configure OpenAI API key for GPT-4V
export OPENAI_API_KEY="sk-your-openai-api-key"

# Configure Gemini API key for Gemini Pro Vision  
export GEMINI_API_KEY="your-gemini-api-key"
```

**Web Interface Access:**
- **Dashboard:** http://localhost:8000/ - Main interface
- **Create Rubrics:** http://localhost:8000/rubrics - Dynamic rubric management
- **Evaluate Submissions:** http://localhost:8000/evaluate - Multimodal evaluation
- **View Reports:** http://localhost:8000/reports - Generated reports
- **API Documentation:** http://localhost:8000/api/docs - Interactive API docs

## ✨ New Features (v2.0.0)
### 📊 Dashboard
Main dashboard, http://localhost:8000/
<img width="1434" height="724" alt="截屏2025-10-19 上午10 00 00" src="https://github.com/user-attachments/assets/95984716-453e-4bf8-9bdf-2159f87019f5" />

### 🔧 Dynamic Rubrics
Create and manage evaluation criteria without code changes via web interface.
- **Setup:** Configure rubrics through web UI at `/rubrics`
- **URL:** http://localhost:8000/rubrics
- **API:** `POST /api/rubrics` for programmatic creation
<img width="1446" height="716" alt="截屏2025-10-19 上午10 00 26" src="https://github.com/user-attachments/assets/2ea60333-48d6-4f98-af92-2198affa3440" />

### 🎨 Multimodal Support  
Evaluate text, images, videos, and audio submissions with AI-powered analysis.
- **Setup:** Upload files via evaluation interface
- **URL:** http://localhost:8000/evaluate  
- **Supported:** JPG, PNG, MP4, MP3, WAV, AVI
- **API:** `POST /api/submissions` for file uploads
- Select model
<img width="1007" height="382" alt="截屏2025-10-19 上午10 29 08" src="https://github.com/user-attachments/assets/fefdd041-0a73-461e-85e0-49d97fabfa5e" />
Get result
<img width="1398" height="713" alt="截屏2025-10-19 上午10 25 48" src="https://github.com/user-attachments/assets/0ed71b90-6406-4258-b26d-ea97f280cf22" />

### 🤖 Backend Integration
GPT-4V, Gemini Pro Vision, and deterministic evaluation modes.
- **Setup:** Configure API keys in `src/api.py` (MODEL_CONFIG)
- **Environment Variables:** `OPENAI_API_KEY`, `GEMINI_API_KEY`
- **API:** `POST /api/evaluate` with `model_provider` parameter

### 📊 Structured Reports
JSON, PDF, and CSV export with detailed analytics and audit trails.
- **Setup:** Reports auto-generated after evaluation
- **URL:** http://localhost:8000/reports
- **API:** `POST /api/reports/generate` for custom reports

### ⚡ Batch Processing
Efficient evaluation of multiple submissions simultaneously.
- **Setup:** Use batch API endpoint for multiple submissions
- **API:** `POST /api/evaluate/batch` with submission array

### 🌐 Web Interface
User-friendly UI for rubric management, evaluation, and results viewing.
- **Setup:** Start web server with `python enhanced_main.py serve`
- **URLs:** 
  - Dashboard: http://localhost:8000/
  - Rubrics: http://localhost:8000/rubrics
  - Evaluate: http://localhost:8000/evaluate  
  - Reports: http://localhost:8000/reports
  - API Docs: http://localhost:8000/api/docs

**Usage Examples:** See `examples/enhanced_usage.py` for detailed code examples

### Option 2: Legacy Deterministic Pipeline

This section demonstrates how to **run the original evaluation demo** and verify the results step by step.

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

### 5. Enhanced Features Overview

#### Dynamic Rubric Management
```bash
# Create rubrics via API
curl -X POST "http://localhost:8000/api/rubrics" \
  -F "rubric_id=creative_writing" \
  -F "name=Creative Writing Evaluation" \
  -F "description=Comprehensive rubric for creative writing" \
  -F 'criteria_json=[{"name":"Creativity","description":"Original thinking","weight":0.4,"threshold":7.0,"category":"creativity"}]'
```

#### Multimodal Submission Evaluation
```python
# Submit multimodal content (text + images)
from src.models import MultimodalSubmission, MediaItem, MediaType

submission = MultimodalSubmission(
    id="submission_001",
    rubric_id="creative_writing",
    media_items=[
        MediaItem(media_type=MediaType.TEXT, content="My creative story..."),
        MediaItem(media_type=MediaType.IMAGE, content="base64_image_data")
    ]
)
```

#### Backend Model Integration
- **OpenAI GPT-4V:** Advanced visual understanding
- **Google Gemini Pro Vision:** Multimodal reasoning
- **Deterministic Mode:** Reproducible baseline evaluation

#### Structured Reports
Generate detailed reports in multiple formats:
- **JSON:** Machine-readable results with full metadata
- **PDF:** Human-readable reports with visualizations
- **CSV:** Tabular data for analysis

### 6. Expected directory structure after running

```
llm-eval-pipeline/
├── README.md
├── LICENSE
├── config.yaml
├── main.py                    # Original deterministic pipeline
├── enhanced_main.py          # New enhanced pipeline
├── requirements.txt
├── src/                      # Enhanced pipeline source code
│   ├── models.py            # Data models
│   ├── rubric_manager.py    # Dynamic rubric management
│   ├── multimodal_evaluator.py  # Evaluation engine
│   ├── report_generator.py  # Report generation
│   ├── api.py              # REST API endpoints
│   ├── web_ui.py           # Web interface
│   └── templates/          # HTML templates
├── examples/
│   ├── input.jsonl
│   └── reproducibility_report.py
├── data/
│   ├── results/            # Evaluation results
│   ├── rubrics/           # Dynamic rubrics storage
│   └── reports/           # Generated reports
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
