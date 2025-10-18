"""
Structured evaluation report generator with multiple export formats.
Supports JSON, PDF, and CSV export options.
"""

import json
import csv
import io
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from jinja2 import Template
except ImportError:
    Template = None

# WeasyPrint is optional and may fail on some systems
try:
    from weasyprint import HTML, CSS
except (ImportError, OSError):
    HTML = None
    CSS = None

from .models import EvaluationResult, DynamicRubric, ReportExportFormat, ReportRequest


class ReportGenerator:
    """Generates structured evaluation reports in multiple formats."""
    
    def __init__(self, output_dir: Path = Path("data/reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_report(self, request: ReportRequest) -> str:
        """Generate a report in the specified format."""
        if request.format == ReportExportFormat.JSON:
            return await self._generate_json_report(request)
        elif request.format == ReportExportFormat.PDF:
            return await self._generate_pdf_report(request)
        elif request.format == ReportExportFormat.CSV:
            return await self._generate_csv_report(request)
        else:
            raise ValueError(f"Unsupported format: {request.format}")
    
    async def _generate_json_report(self, request: ReportRequest) -> str:
        """Generate JSON report."""
        report_data = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "rubric_id": request.rubric.id,
                "rubric_name": request.rubric.name,
                "total_submissions": len(request.evaluation_results),
                "format": "json"
            },
            "rubric": request.rubric.model_dump(mode='json'),
            "evaluation_results": [result.model_dump(mode='json') for result in request.evaluation_results],
        }
        
        if request.include_metadata:
            report_data["report_metadata"].update({
                "pipeline_version": "2.0.0",
                "generated_by": "llm-eval-pipeline",
            })
        
        return json.dumps(report_data, indent=2, default=str)
    
    async def _generate_csv_report(self, request: ReportRequest) -> str:
        """Generate CSV report."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        header = [
            "submission_id", "overall_score", "passed", "evaluated_at", 
            "processing_time_ms", "model_provider"
        ]
        
        # Add columns for each criterion
        for criterion in request.rubric.criteria:
            header.extend([
                f"{criterion.name}_score",
                f"{criterion.name}_feedback",
                f"{criterion.name}_threshold"
            ])
        
        writer.writerow(header)
        
        # Data rows
        for result in request.evaluation_results:
            row = [
                result.submission_id,
                result.overall_score,
                result.passed,
                result.evaluated_at.isoformat(),
                result.processing_time_ms,
                result.model_provider.value
            ]
            
            # Add criterion scores
            for criterion in request.rubric.criteria:
                criterion_score = next(
                    (score for score in result.criterion_scores 
                     if score.criterion_name == criterion.name),
                    None
                )
                
                if criterion_score:
                    row.extend([
                        criterion_score.score,
                        criterion_score.feedback,
                        criterion.threshold
                    ])
                else:
                    row.extend(["", "", criterion.threshold])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    async def _generate_pdf_report(self, request: ReportRequest) -> str:
        """Generate PDF report."""
        if HTML is None or Template is None:
            raise ImportError("PDF generation requires jinja2 and weasyprint packages")
        
        # Prepare data for template
        template_data = {
            "rubric": request.rubric,
            "results": request.evaluation_results,
            "metadata": {
                "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "total_submissions": len(request.evaluation_results),
                "rubric_name": request.rubric.name
            }
        }
        
        # HTML template for PDF
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>LLM Evaluation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }
                .rubric-info { background: #f5f5f5; padding: 20px; margin: 20px 0; }
                .result { border: 1px solid #ccc; margin: 20px 0; padding: 20px; }
                .criterion { margin: 10px 0; padding: 10px; background: #fafafa; }
                .score { font-weight: bold; color: #0066cc; }
                .passed { color: #009900; }
                .failed { color: #cc0000; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>LLM Evaluation Report</h1>
                <p>Generated on {{ metadata.generated_at }}</p>
            </div>
            
            <div class="rubric-info">
                <h2>Rubric: {{ rubric.name }}</h2>
                <p>{{ rubric.description }}</p>
                <h3>Criteria:</h3>
                <ul>
                {% for criterion in rubric.criteria %}
                    <li><strong>{{ criterion.name }}</strong> (Weight: {{ criterion.weight }}, Threshold: {{ criterion.threshold }}/10)<br>
                    {{ criterion.description }}</li>
                {% endfor %}
                </ul>
            </div>
            
            <h2>Evaluation Results ({{ metadata.total_submissions }} submissions)</h2>
            
            {% for result in results %}
            <div class="result">
                <h3>Submission {{ result.submission_id }}</h3>
                <p><span class="score">Overall Score: {{ "%.2f"|format(result.overall_score) }}/10</span> 
                   <span class="{% if result.passed %}passed{% else %}failed{% endif %}">
                   ({{ "PASSED" if result.passed else "FAILED" }})
                   </span>
                </p>
                <p>Model: {{ result.model_provider.value }} | 
                   Processing Time: {{ result.processing_time_ms }}ms | 
                   Evaluated: {{ result.evaluated_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
                
                <h4>Criterion Scores:</h4>
                {% for criterion_score in result.criterion_scores %}
                <div class="criterion">
                    <strong>{{ criterion_score.criterion_name }}:</strong> 
                    <span class="score">{{ "%.2f"|format(criterion_score.score) }}/10</span><br>
                    <strong>Feedback:</strong> {{ criterion_score.feedback }}<br>
                    <strong>Reasoning:</strong> {{ criterion_score.reasoning }}
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        # Generate PDF (this would need to be saved to a file in practice)
        # For now, return the HTML content as a placeholder
        return html_content
    
    def save_report(self, content: str, filename: str, format: ReportExportFormat) -> Path:
        """Save report to file."""
        if format == ReportExportFormat.PDF:
            file_path = self.output_dir / f"{filename}.pdf"
            # In practice, you'd use weasyprint to generate actual PDF
            # For now, save as HTML for demonstration
            file_path = self.output_dir / f"{filename}.html"
        elif format == ReportExportFormat.JSON:
            file_path = self.output_dir / f"{filename}.json"
        elif format == ReportExportFormat.CSV:
            file_path = self.output_dir / f"{filename}.csv"
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        
        return file_path
    
    def generate_summary_statistics(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Generate summary statistics for evaluation results."""
        if not results:
            return {}
        
        scores = [result.overall_score for result in results]
        passed_count = sum(1 for result in results if result.passed)
        
        return {
            "total_submissions": len(results),
            "passed_submissions": passed_count,
            "pass_rate": passed_count / len(results) if results else 0,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "average_processing_time_ms": sum(r.processing_time_ms for r in results) / len(results)
        }
