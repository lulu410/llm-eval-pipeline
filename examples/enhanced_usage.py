#!/usr/bin/env python3
"""
Enhanced LLM Evaluation Pipeline Usage Examples.
Demonstrates how to use the new multimodal evaluation features.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models import (
    DynamicRubric, RubricCriterion, MultimodalSubmission, 
    MediaItem, MediaType, EvaluationRequest, ModelProvider,
    ReportRequest, ReportExportFormat
)
from src.rubric_manager import RubricManager
from src.multimodal_evaluator import MultimodalEvaluator
from src.report_generator import ReportGenerator


async def example_creative_writing_evaluation():
    """Example: Evaluate a creative writing submission with images."""
    
    print("🎨 Creative Writing Evaluation Example")
    print("-" * 40)
    
    # 1. Create or load a rubric
    rubric_manager = RubricManager()
    
    # Check if rubric exists, create if not
    rubric = rubric_manager.get_rubric("creative_writing_basic")
    if not rubric:
        criteria = [
            RubricCriterion(
                name="Story Structure",
                description="Clear beginning, middle, and end with logical flow",
                weight=0.25,
                threshold=6.0,
                category="narrative"
            ),
            RubricCriterion(
                name="Character Development", 
                description="Well-developed, believable characters with clear motivations",
                weight=0.25,
                threshold=6.0,
                category="characterization"
            ),
            RubricCriterion(
                name="Creativity & Originality",
                description="Fresh ideas, unique voice, innovative approach",
                weight=0.3,
                threshold=7.0,
                category="creativity"
            ),
            RubricCriterion(
                name="Writing Quality",
                description="Grammar, style, clarity, and engaging prose",
                weight=0.2,
                threshold=6.5,
                category="technical"
            )
        ]
        
        rubric = rubric_manager.create_rubric(
            "creative_writing_basic",
            "Basic Creative Writing Evaluation",
            "Comprehensive rubric for evaluating short story submissions",
            criteria
        )
        print(f"✓ Created rubric: {rubric.name}")
    
    # 2. Create a multimodal submission
    story_text = """
    The Last Library
    
    In the year 2147, where knowledge was stored in clouds of light 
    and information flowed through neural networks, there stood one 
    last building made of stone and filled with paper books. 
    
    Maya had discovered it by accident while exploring the forbidden 
    zones of the city. The library was older than the Great Upload, 
    older than the AI consciousness that now governed humanity's 
    collective memory.
    
    As she ran her fingers along the cracked spines of forgotten 
    novels, she realized that some stories were meant to be touched, 
    not just downloaded into your mind.
    """
    
    # Create submission with text and an image description
    submission = MultimodalSubmission(
        id="story_submission_001",
        rubric_id=rubric.id,
        media_items=[
            MediaItem(
                media_type=MediaType.TEXT,
                content=story_text,
                metadata={
                    "word_count": len(story_text.split()),
                    "genre": "science_fiction",
                    "author_notes": "A story about preserving physical books in a digital future"
                }
            ),
            MediaItem(
                media_type=MediaType.IMAGE,
                content="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjOGJjNGVmIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzMzMyIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkxpYnJhcnkgSWxsdXN0cmF0aW9uPC90ZXh0Pjwvc3ZnPg==",
                metadata={
                    "caption": "Illustration of a futuristic library",
                    "style": "digital_art",
                    "colors": "blue_theme"
                }
            )
        ]
    )
    
    print(f"✓ Created submission with {len(submission.media_items)} media items")
    
    # 3. Evaluate the submission
    evaluator = MultimodalEvaluator(model_config={})
    
    # Use deterministic evaluation for reproducible results
    result = await evaluator.evaluate_submission(
        submission, 
        rubric, 
        ModelProvider.DETERMINISTIC
    )
    
    print(f"\n📊 Evaluation Results:")
    print(f"   Overall Score: {result.overall_score:.2f}/10")
    print(f"   Passed: {'✅' if result.passed else '❌'}")
    print(f"   Processing Time: {result.processing_time_ms}ms")
    
    print(f"\n📋 Detailed Scores:")
    for score in result.criterion_scores:
        threshold = next(c.threshold for c in rubric.criteria if c.name == score.criterion_name)
        status = "✅" if score.score >= threshold else "❌"
        print(f"   {score.criterion_name}: {score.score:.2f}/10 (threshold: {threshold}) {status}")
        print(f"      Feedback: {score.feedback}")
    
    # 4. Generate a report
    report_generator = ReportGenerator()
    
    report_request = ReportRequest(
        evaluation_results=[result],
        rubric=rubric,
        format=ReportExportFormat.JSON,
        include_metadata=True
    )
    
    report_content = await report_generator.generate_report(report_request)
    report_path = report_generator.save_report(
        report_content, 
        "creative_writing_example_report", 
        ReportExportFormat.JSON
    )
    
    print(f"\n📄 Report generated: {report_path}")
    
    return result


async def example_batch_evaluation():
    """Example: Batch evaluation of multiple submissions."""
    
    print("\n\n⚡ Batch Evaluation Example")
    print("-" * 40)
    
    # This would be used with the API for batch processing
    # For now, just demonstrate the concept
    
    print("Batch evaluation would process multiple submissions:")
    print("- submission_001: Creative writing story")
    print("- submission_002: Poetry with illustration") 
    print("- submission_003: Script with storyboard images")
    print("\nEach submission would be evaluated against the same rubric")
    print("and results would be aggregated in a comprehensive report.")


async def main():
    """Run the enhanced pipeline examples."""
    
    print("Enhanced LLM Evaluation Pipeline - Usage Examples")
    print("=" * 60)
    
    # Run the creative writing example
    await example_creative_writing_evaluation()
    
    # Show batch evaluation concept
    await example_batch_evaluation()
    
    print("\n" + "=" * 60)
    print("🎉 Examples completed!")
    print("\nNext steps:")
    print("1. Start the web server: python enhanced_main.py serve")
    print("2. Visit http://localhost:8000 to use the web UI")
    print("3. Explore the API at http://localhost:8000/api/docs")


if __name__ == "__main__":
    asyncio.run(main())
