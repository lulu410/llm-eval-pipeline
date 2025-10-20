# LLM Evaluation Pipeline - Hugging Face Space

**Deterministic, reproducible evaluation with verifiable artifacts**  
Aligned with U.S. EO 14110 and NIST AI RMF framework.

## Run in 60 Seconds

1. **Click the Space** - The demo is ready to run
2. **Enter text** - Use the sample text or provide your own
3. **Configure settings** (optional) - Adjust seed, runs, thresholds
4. **Run Evaluation** - Get deterministic results instantly
5. **Download artifacts** - JSON, PDF, and verification hashes

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

### Governance Features

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