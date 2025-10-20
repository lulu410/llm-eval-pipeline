# file: app.py
"""
Hugging Face Space for LLM Evaluation Pipeline
Deterministic, reproducible evaluation demo with verifiable artifacts.
"""

import gradio as gr
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

from utils.determinism import run_deterministic_evaluation
from utils.io import save_artifacts, load_sample_text
from utils.schema import EvaluationResult, EvaluationConfig


def evaluate_text(
    text_content: str,
    org_name: str,
    seed: int,
    runs: int,
    repro_threshold: float,
    variance_threshold: float,
    doi: str
) -> tuple[str, str, str, str]:
    """Run deterministic evaluation and return results."""
    
    if not text_content.strip():
        return "Please provide some text to evaluate.", "", "", ""
    
    try:
        # Create config
        config = EvaluationConfig(
            seed=seed,
            runs=runs,
            reproducibility_threshold=repro_threshold,
            variance_threshold=variance_threshold,
            org_name=org_name.strip() if org_name else None,
            doi=doi.strip() if doi else None
        )
        
        # Run evaluation
        result = run_deterministic_evaluation(text_content, config)
        
        # Save artifacts
        json_path, pdf_path = save_artifacts(result)
        
        # Format JSON preview
        json_preview = result.model_dump()
        
        # Generate verification line
        verification_line = f"results.json SHA256: {result.results_sha256}"
        
        return (
            json_preview,
            verification_line,
            json_path if json_path.exists() else None,
            pdf_path if pdf_path.exists() else None
        )
        
    except Exception as e:
        return f"Evaluation failed: {str(e)}", "", "", ""


def handle_file_upload(file):
    """Handle file upload and return content."""
    if file is not None:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except:
            try:
                # Try as binary for images
                with open(file, 'rb') as f:
                    content = f.read()
                return f"[Image file uploaded: {len(content)} bytes]"
            except:
                return "Could not read uploaded file."
    return load_sample_text()


def create_interface():
    """Create the Gradio interface."""
    
    # Load sample text
    sample_text = load_sample_text()
    
    with gr.Blocks(title="LLM Evaluation Pipeline", theme=gr.themes.Default()) as demo:
        gr.Markdown("""
        # LLM Evaluation Pipeline
        
        **Deterministic, reproducible evaluation with verifiable artifacts**  
        Aligned with U.S. EO 14110 and NIST AI RMF framework.
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Text to Evaluate",
                    value=sample_text,
                    lines=8,
                    placeholder="Enter text to evaluate or upload a file..."
                )
                
                file_input = gr.File(
                    label="Upload File (optional)",
                    file_types=["text", "image"]
                )
                
            with gr.Column(scale=1):
                org_name = gr.Textbox(
                    label="Organization Name (optional)",
                    placeholder="e.g., ACME Corp"
                )
                
                doi_input = gr.Textbox(
                    label="DOI (optional)",
                    placeholder="e.g., 10.1234/example"
                )
                
                seed_input = gr.Number(
                    label="Seed",
                    value=20251020,
                    precision=0
                )
                
                runs_input = gr.Number(
                    label="Runs",
                    value=5,
                    precision=0,
                    minimum=1,
                    maximum=100
                )
                
                repro_threshold = gr.Slider(
                    label="Reproducibility Threshold",
                    value=0.90,
                    minimum=0.1,
                    maximum=1.0,
                    step=0.01
                )
                
                variance_threshold = gr.Slider(
                    label="Variance Threshold",
                    value=0.05,
                    minimum=0.001,
                    maximum=0.5,
                    step=0.001
                )
        
        run_button = gr.Button("Run Evaluation", variant="primary", size="lg")
        
        with gr.Row():
            with gr.Column():
                json_preview = gr.JSON(label="Results Preview")
                verification = gr.Textbox(label="Verification", interactive=False)
                
            with gr.Column():
                download_json = gr.File(label="Download JSON")
                download_pdf = gr.File(label="Download PDF")
        
        # Handle file upload
        file_input.change(handle_file_upload, inputs=[file_input], outputs=[text_input])
        
        # Handle evaluation
        run_button.click(
            evaluate_text,
            inputs=[
                text_input, org_name, seed_input, runs_input,
                repro_threshold, variance_threshold, doi_input
            ],
            outputs=[json_preview, verification, download_json, download_pdf]
        )
        
        gr.Markdown("""
        ## How to Verify
        
        1. Note the timestamp and SHA256 hash displayed above
        2. Run the same evaluation with identical inputs - you should get identical results
        3. Download and verify the JSON and PDF artifacts
        4. The SHA256 hash provides cryptographic provenance for all results
        """)
    
    return demo


if __name__ == "__main__":
    demo = create_interface()
    
    # Hugging Face Spaces configuration
    import os
    if os.getenv("SPACE_ID"):  # Running on Hugging Face Spaces
        demo.launch()  # Use default settings for Spaces
    else:
        demo.launch(server_name="0.0.0.0", server_port=7860)  # Local development
