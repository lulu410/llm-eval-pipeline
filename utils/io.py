# file: utils/io.py
"""
I/O utilities for saving artifacts and handling files.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import qrcode
from io import BytesIO

from .schema import EvaluationResult


def calculate_sha256(data: str) -> str:
    """Calculate SHA256 hash of string data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def ensure_data_dir():
    """Ensure data directory exists."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def load_sample_text() -> str:
    """Load sample text from examples directory."""
    sample_path = Path("examples/sample_text.txt")
    if sample_path.exists():
        return sample_path.read_text(encoding='utf-8')
    return "Reliable evaluation demo text."


def save_results_json(result: EvaluationResult, data_dir: Path) -> Path:
    """Save results to JSON file."""
    json_path = data_dir / "results.json"
    
    # Convert to dict and handle datetime serialization
    result_dict = result.model_dump()
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
    
    return json_path


def save_run_log(result: EvaluationResult, data_dir: Path) -> Path:
    """Save human-readable run log."""
    log_path = data_dir / "run.log"
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"LLM Evaluation Pipeline - Run Log\n")
        f.write(f"Timestamp: {result.timestamp_utc}\n")
        f.write(f"Organization: {result.org_name or 'Not specified'}\n")
        f.write(f"DOI: {result.doi or 'Not specified'}\n")
        f.write(f"Input SHA256: {result.input_sha256}\n")
        f.write(f"Config SHA256: {result.config_sha256}\n")
        f.write(f"Results SHA256: {result.results_sha256}\n")
        f.write(f"Seed: {result.seed}, Runs: {result.runs}\n")
        f.write(f"Reproducibility: {result.reproducibility_score:.3f} ({'PASS' if result.reproducibility_passed else 'FAIL'})\n")
        f.write(f"Variance: {result.latency_variance_ratio:.3f} ({'PASS' if result.variance_passed else 'FAIL'})\n")
        f.write(f"Overall: {'PASS' if result.overall_passed else 'FAIL'}\n")
    
    return log_path


def create_qr_code(data: str) -> bytes:
    """Create QR code image as bytes."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()


def save_pdf_report(result: EvaluationResult, data_dir: Path) -> Path:
    """Generate and save PDF report."""
    pdf_path = data_dir / "report.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Content
    story = []
    
    # Title
    title = "LLM Evaluation Pipeline Report"
    if result.org_name:
        title += f" - {result.org_name}"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    # Basic info
    basic_data = [
        ['Timestamp', result.timestamp_utc],
        ['Organization', result.org_name or 'Not specified'],
        ['DOI', result.doi or 'Not specified'],
    ]
    
    basic_table = Table(basic_data, colWidths=[2*inch, 4*inch])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("Evaluation Information", styles['Heading2']))
    story.append(basic_table)
    story.append(Spacer(1, 20))
    
    # Results
    results_data = [
        ['Metric', 'Value', 'Threshold', 'Status'],
        ['Reproducibility Score', f"{result.reproducibility_score:.3f}", f"{result.reproducibility_threshold:.3f}", 
         'PASS' if result.reproducibility_passed else 'FAIL'],
        ['Latency Variance Ratio', f"{result.latency_variance_ratio:.3f}", f"{result.variance_threshold:.3f}", 
         'PASS' if result.variance_passed else 'FAIL'],
        ['Overall Status', '', '', 'PASS' if result.overall_passed else 'FAIL'],
    ]
    
    results_table = Table(results_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("Evaluation Results", styles['Heading2']))
    story.append(results_table)
    story.append(Spacer(1, 20))
    
    # Hash verification
    hash_data = [
        ['Hash Type', 'Value'],
        ['Input SHA256', result.input_sha256],
        ['Config SHA256', result.config_sha256],
        ['Results SHA256', result.results_sha256],
    ]
    
    hash_table = Table(hash_data, colWidths=[2*inch, 4*inch])
    hash_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("Cryptographic Verification", styles['Heading2']))
    story.append(hash_table)
    
    # QR Code
    if result.doi:
        qr_data = result.doi
        qr_text = f"DOI: {result.doi}"
    else:
        qr_data = "https://github.com/lulu410/llm-eval-pipeline"
        qr_text = "Project Repository"
    
    try:
        qr_img_bytes = create_qr_code(qr_data)
        # For now, just add text since handling images in reportlab is complex
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"QR Code: {qr_text}", styles['Normal']))
        story.append(Paragraph(f"URL: {qr_data}", styles['Normal']))
    except Exception as e:
        story.append(Paragraph(f"QR Code generation failed: {str(e)}", styles['Normal']))
    
    doc.build(story)
    return pdf_path


def save_artifacts(result: EvaluationResult) -> Tuple[Path, Path]:
    """Save all artifacts (JSON, log, PDF)."""
    data_dir = ensure_data_dir()
    
    json_path = save_results_json(result, data_dir)
    save_run_log(result, data_dir)
    pdf_path = save_pdf_report(result, data_dir)
    
    return json_path, pdf_path
