# LLM Evaluation Pipeline - Hugging Face Space

**Deterministic, reproducible evaluation with verifiable artifacts**  
Aligned with U.S. EO 14110 and NIST AI RMF framework.

## 🚀 How to Run This Demo

### Option 1: Live Demo (Recommended)
1. **Visit**: https://huggingface.co/spaces/madison-xu/llm-eval-pipeline-art
2. **Wait for loading** (30-60 seconds)
3. **Enter text and photo** in the text box
4. **Click "Run Evaluation"** (blue button)
5. **Download** JSON reports

### Option 2: Run the Enhanced Pipeline
```bash
# Clone the repository
git clone https://github.com/lulu410/llm-eval-pipeline.git
cd llm-eval-pipeline

# Install ALL dependencies (one command)
pip install -r requirements.txt

# Start the web server
python3 enhanced_main.py serve

# Access the full interface at http://localhost:8000
```

## 📖 Detailed Usage Instructions

### For the Hugging Face Space Demo:

1. **Text Input**:
   - Type your text in the large text area
   - Or click "Upload File" to upload a text/image file
   - Sample text is pre-filled for testing

2. **Optional Configuration**:
   - **Organization Name**: Your company name (appears in reports)
   - **DOI**: Digital Object Identifier (creates QR code in PDF)
   - **Seed**: Random seed for reproducibility (default: 20251020)
   - **Runs**: Number of evaluation runs (default: 5)
   - **Reproducibility Threshold**: Minimum score to pass (default: 0.90)
   - **Variance Threshold**: Maximum variance ratio (default: 0.05)

3. **Run Evaluation**:
   - Click the **"Run Evaluation"** button
   - Wait 1-2 seconds for processing
   - Results appear below

4. **View Results**:
   - **JSON Preview**: See all metrics in the interface
   - **Verification Hash**: SHA256 hash for verification
   - **Download JSON**: Complete results.json file
   - **Download PDF**: Professional report.pdf

### For the Enhanced Pipeline:

1. **Start the server**: `python enhanced_main.py serve`
2. **Access dashboard**: http://localhost:8000/
3. **Create rubrics**: http://localhost:8000/rubrics/create
4. **Evaluate submissions**: http://localhost:8000/evaluate
5. **View reports**: http://localhost:8000/reports

## What's Different

This pipeline produces **deterministic results** - identical inputs always produce identical outputs. This is achieved through cryptographic hashing (SHA256) rather than external AI API calls.

### How Determinism Works

- **Seed-based**: Results depend only on your input text and seed value
- **SHA256 Provenance**: Every result includes cryptographic hashes for verification
- **Reproducible**: Same inputs = same outputs, always
- **No API Keys**: Works completely offline

### Generated Artifacts

Each evaluation creates three files in the `data/` directory:

1. **`results.json`** - Complete metrics, thresholds, and hashes
2. **`run.log`** - Human-readable log with summary
3. **`report.pdf`** - Professional report with verification details

### Verification Process

To verify any evaluation:

1. **Record the inputs**: Save the text, seed, and run parameters used
2. **Note the timestamp**: UTC ISO-8601 format with Z suffix
3. **Save the SHA256**: The `results.json` SHA256 hash provides cryptographic proof
4. **Re-run**: Use identical inputs - you'll get identical results

## Policy Alignment

This system aligns with:

- **U.S. Executive Order 14110**: Safe, secure, and trustworthy AI development
- **NIST AI RMF 1.0**: Govern, Map, Measure, and Manage AI risks

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

- **Transparent process**: All evaluation steps are deterministic and documented
- **Audit trail**: Complete provenance information for every result
- **Verifiable artifacts**: Cryptographic hashes ensure result integrity
- **Reproducible outcomes**: Consistent results across different environments

## Verification Ledger

### How Others Can Confirm Results

To verify that an evaluation was conducted properly, external users can:

1. **Request verification**: Provide the timestamp, SHA256 hash, and inputs used
2. **Independent reproduction**: Run the same evaluation with identical parameters
3. **Hash comparison**: Verify that the SHA256 hashes match exactly
4. **Report generation**: Confirm that downloadable reports are identical

### Reporting Issues

If you encounter discrepancies or have questions about results:

- **GitHub Issues**: Report technical problems or request verification
- **Email**: Contact the development team with evaluation concerns
- **Documentation**: Provide timestamp, SHA256, and input parameters for investigation

## Technical Details

- **Language**: Python 3.11+
- **Framework**: Gradio for UI, Pydantic for validation
- **Hashing**: SHA256 for all cryptographic operations
- **Standards**: ISO-8601 timestamps, UTF-8 encoding
- **Dependencies**: Minimal external requirements

## Contact

For questions about this evaluation pipeline or to request verification of results, please reach out through the project repository or contact the development team.