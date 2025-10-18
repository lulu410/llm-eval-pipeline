#!/usr/bin/env python3
"""
Test script to verify the enhanced LLM evaluation pipeline features.
This script tests the core functionality without requiring external API keys.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import (
    DynamicRubric, RubricCriterion, MultimodalSubmission, 
    MediaItem, MediaType, ModelProvider
)
from src.rubric_manager import RubricManager


def test_rubric_management():
    """Test dynamic rubric creation and management."""
    print("Testing Dynamic Rubric Management...")
    
    rubric_manager = RubricManager(Path("test_data/rubrics"))
    
    # Create test criteria
    criteria = [
        RubricCriterion(
            name="Creativity",
            description="Evaluates originality and innovative thinking",
            weight=0.4,
            threshold=6.0,
            category="creativity"
        ),
        RubricCriterion(
            name="Clarity",
            description="Assesses clear communication and understanding", 
            weight=0.6,
            threshold=7.0,
            category="communication"
        )
    ]
    
    # Test rubric creation
    rubric = rubric_manager.create_rubric(
        "test_rubric",
        "Test Evaluation Rubric",
        "A test rubric for validation",
        criteria
    )
    
    assert rubric.name == "Test Evaluation Rubric"
    assert len(rubric.criteria) == 2
    assert rubric_manager.validate_rubric_weights("test_rubric")
    
    # Test rubric retrieval
    retrieved_rubric = rubric_manager.get_rubric("test_rubric")
    assert retrieved_rubric is not None
    assert retrieved_rubric.id == "test_rubric"
    
    print("✓ Rubric management tests passed")


def test_multimodal_submission():
    """Test multimodal submission creation."""
    print("Testing Multimodal Submission Creation...")
    
    # Create test submission
    submission = MultimodalSubmission(
        id="test_submission_001",
        rubric_id="test_rubric",
        media_items=[
            MediaItem(
                media_type=MediaType.TEXT,
                content="This is a test creative writing submission.",
                metadata={"word_count": 8, "language": "en"}
            ),
            MediaItem(
                media_type=MediaType.IMAGE,
                content="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBvaGVpZ2h0PSIyMDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2YwZjBmMCIvPjwvc3ZnPg==",
                filename="test_image.svg",
                metadata={"format": "svg", "size": "200x200"}
            )
        ]
    )
    
    assert submission.id == "test_submission_001"
    assert len(submission.media_items) == 2
    assert submission.media_items[0].media_type == MediaType.TEXT
    assert submission.media_items[1].media_type == MediaType.IMAGE
    
    print("✓ Multimodal submission tests passed")


def test_model_providers():
    """Test model provider enum."""
    print("Testing Model Providers...")
    
    providers = [ModelProvider.DETERMINISTIC, ModelProvider.OPENAI, ModelProvider.GOOGLE_GEMINI]
    
    for provider in providers:
        assert provider.value in ["deterministic", "openai", "google_gemini"]
    
    print("✓ Model provider tests passed")


def main():
    """Run all tests."""
    print("Enhanced LLM Evaluation Pipeline - Feature Tests")
    print("=" * 50)
    
    try:
        test_rubric_management()
        test_multimodal_submission() 
        test_model_providers()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Enhanced features are working correctly.")
        print("\nTo run the full pipeline:")
        print("1. python enhanced_main.py demo     # Run demo")
        print("2. python enhanced_main.py serve    # Start web server")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
