#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced LLM Evaluation Pipeline with multimodal support.
This is the new main entry point that supports:
- Dynamic rubric management
- Multimodal submission evaluation
- Backend model integration (GPT-4V, Gemini Pro Vision)
- Structured report generation
- Web API and UI interfaces
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import (
    MultimodalSubmission, MediaItem, MediaType, DynamicRubric, 
    RubricCriterion, EvaluationRequest, ModelProvider, ReportRequest,
    ReportExportFormat
)
from src.rubric_manager import RubricManager
from src.multimodal_evaluator import MultimodalEvaluator
from src.report_generator import ReportGenerator


async def create_sample_rubric(rubric_manager: RubricManager):
    """Create a sample rubric for testing."""
    sample_criteria = [
        RubricCriterion(
            name="Creativity",
            description="Evaluates originality and innovative thinking",
            weight=0.3,
            threshold=6.0,
            category="creativity"
        ),
        RubricCriterion(
            name="Clarity",
            description="Assesses clear communication and understanding",
            weight=0.4,
            threshold=7.0,
            category="communication"
        ),
        RubricCriterion(
            name="Technical Quality",
            description="Evaluates technical execution and craftsmanship",
            weight=0.3,
            threshold=5.0,
            category="technical"
        )
    ]
    
    try:
        rubric = rubric_manager.create_rubric(
            "sample_multimodal_rubric",
            "Sample Multimodal Evaluation Rubric",
            "A comprehensive rubric for evaluating multimodal creative works including text, images, and video",
            sample_criteria
        )
        print(f"[✓] Created sample rubric: {rubric.name}")
        return rubric
    except ValueError:
        # Rubric already exists
        rubric = rubric_manager.get_rubric("sample_multimodal_rubric")
        print(f"[i] Using existing rubric: {rubric.name}")
        return rubric


async def run_multimodal_evaluation():
    """Run a multimodal evaluation demo."""
    print("Enhanced LLM Evaluation Pipeline - Multimodal Demo")
    print("=" * 50)
    
    # Initialize components
    rubric_manager = RubricManager()
    report_generator = ReportGenerator()
    model_config = {
        "openai": {"api_key": "demo-key"},
        "google_gemini": {"api_key": "demo-key"}
    }
    
    # Create sample rubric
    rubric = await create_sample_rubric(rubric_manager)
    
    # Create sample multimodal submission
    sample_text = "This is a creative story about AI and human collaboration in the future."
    
    # Create a sample image data (base64 encoded placeholder)
    sample_image_data = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzMzMyIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPlNhbXBsZSBJbWFnZTwvdGV4dD48L3N2Zz4="
    
    submission = MultimodalSubmission(
        id="demo_submission_001",
        rubric_id=rubric.id,
        media_items=[
            MediaItem(
                media_type=MediaType.TEXT,
                content=sample_text,
                metadata={"source": "user_input", "language": "en"}
            ),
            MediaItem(
                media_type=MediaType.IMAGE,
                content=sample_image_data,
                metadata={"caption": "Sample creative illustration", "source": "generated"}
            )
        ]
    )
    
    print(f"[i] Created sample submission with {len(submission.media_items)} media items")
    
    # Run evaluation with deterministic model first
    evaluator = MultimodalEvaluator(model_config)
    
    print("\n[1] Running deterministic evaluation...")
    request = EvaluationRequest(
        submission=submission,
        model_provider=ModelProvider.DETERMINISTIC,
        config={}
    )
    
    result = await evaluator.evaluate_submission(submission, rubric, ModelProvider.DETERMINISTIC)
    
    print(f"[✓] Evaluation completed in {result.processing_time_ms}ms")
    print(f"    Overall Score: {result.overall_score:.2f}/10")
    print(f"    Passed: {'✓' if result.passed else '✗'}")
    print("\n    Criterion Scores:")
    for score in result.criterion_scores:
        status = "✓" if score.score >= next(c.threshold for c in rubric.criteria if c.name == score.criterion_name) else "✗"
        print(f"      {score.criterion_name}: {score.score:.2f}/10 {status}")
    
    # Generate report
    print("\n[2] Generating structured report...")
    report_request = ReportRequest(
        evaluation_results=[result],
        rubric=rubric,
        format=ReportExportFormat.JSON,
        include_metadata=True
    )
    
    report_content = await report_generator.generate_report(report_request)
    report_path = report_generator.save_report(report_content, "demo_evaluation_report", ReportExportFormat.JSON)
    
    print(f"[✓] Report saved to: {report_path}")
    
    # Print summary statistics
    stats = report_generator.generate_summary_statistics([result])
    print(f"\n[3] Summary Statistics:")
    print(f"    Total Submissions: {stats['total_submissions']}")
    print(f"    Pass Rate: {stats['pass_rate']:.1%}")
    print(f"    Average Score: {stats['average_score']:.2f}/10")
    
    print("\n[✓] Enhanced evaluation demo completed successfully!")
    print("\nTo start the web interface, run:")
    print("  python enhanced_main.py serve")


async def start_web_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the web server with API and UI."""
    import uvicorn
    from src.web_ui import app
    
    print(f"Starting LLM Evaluation Pipeline web server...")
    print(f"Web UI: http://{host}:{port}/")
    print(f"API Documentation: http://{host}:{port}/api/docs")
    
    config = uvicorn.Config(
        app, 
        host=host, 
        port=port, 
        reload=True,
        reload_dirs=["src", "templates"],
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced LLM Evaluation Pipeline with multimodal support"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run multimodal evaluation demo")
    
    # Web server command
    server_parser = subparsers.add_parser("serve", help="Start web server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    # Legacy compatibility
    legacy_parser = subparsers.add_parser("legacy", help="Run original deterministic pipeline")
    legacy_parser.add_argument("--config", "-c", default="config.yaml", help="Path to config.yaml")
    
    args = parser.parse_args()
    
    if args.command == "demo":
        asyncio.run(run_multimodal_evaluation())
    elif args.command == "serve":
        asyncio.run(start_web_server(args.host, args.port))
    elif args.command == "legacy":
        # Import and run the original main.py
        import main as legacy_main
        legacy_main.main()
    else:
        # Default to demo if no command specified
        asyncio.run(run_multimodal_evaluation())


if __name__ == "__main__":
    main()
