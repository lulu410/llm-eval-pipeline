#!/usr/bin/env python3
"""
Create sample rubrics for MVP testing.
"""

import json
from pathlib import Path
from src.models import DynamicRubric, RubricCriterion
from datetime import datetime

def create_sample_rubrics():
    """Create sample rubrics for AI Arts evaluation."""
    
    # Digital Art Rubric
    digital_art_rubric = DynamicRubric(
        id="digital_art_evaluation",
        name="Digital Art Evaluation",
        description="Specialized rubric for digital and AI-generated artwork",
        criteria=[
            RubricCriterion(
                name="Visual Composition",
                description="Balance, harmony, and visual flow of the composition",
                weight=0.30,
                threshold=6.0,
                category="Composition"
            ),
            RubricCriterion(
                name="Color Harmony",
                description="Effective use of color, contrast, and visual appeal",
                weight=0.25,
                threshold=5.5,
                category="Color Theory"
            ),
            RubricCriterion(
                name="Detail & Resolution",
                description="Level of detail, resolution quality, and technical precision",
                weight=0.20,
                threshold=6.0,
                category="Technical Quality"
            ),
            RubricCriterion(
                name="Emotional Impact",
                description="Ability to evoke emotions and create connection with viewer",
                weight=0.15,
                threshold=5.0,
                category="Emotional Response"
            ),
            RubricCriterion(
                name="Originality",
                description="Uniqueness and creative originality of the work",
                weight=0.10,
                threshold=5.5,
                category="Creativity"
            )
        ]
    )
    
    # Creative Writing Rubric
    creative_writing_rubric = DynamicRubric(
        id="creative_writing",
        name="Creative Writing Evaluation",
        description="Rubric for evaluating creative writing and storytelling",
        criteria=[
            RubricCriterion(
                name="Narrative Structure",
                description="Plot development, pacing, and story organization",
                weight=0.25,
                threshold=6.0,
                category="Structure"
            ),
            RubricCriterion(
                name="Character Development",
                description="Character depth, motivation, and believability",
                weight=0.20,
                threshold=5.5,
                category="Characterization"
            ),
            RubricCriterion(
                name="Writing Style",
                description="Prose quality, voice, and literary techniques",
                weight=0.20,
                threshold=6.0,
                category="Style"
            ),
            RubricCriterion(
                name="Imagination",
                description="Creative ideas, world-building, and originality",
                weight=0.20,
                threshold=5.5,
                category="Creativity"
            ),
            RubricCriterion(
                name="Emotional Resonance",
                description="Ability to connect with readers emotionally",
                weight=0.15,
                threshold=5.0,
                category="Impact"
            )
        ]
    )
    
    # Video Content Rubric
    video_content_rubric = DynamicRubric(
        id="video_content",
        name="Video Content Evaluation",
        description="Rubric for evaluating video content and multimedia submissions",
        criteria=[
            RubricCriterion(
                name="Visual Storytelling",
                description="Effectiveness of visual narrative and story flow",
                weight=0.25,
                threshold=6.0,
                category="Narrative"
            ),
            RubricCriterion(
                name="Production Quality",
                description="Video quality, editing, and technical execution",
                weight=0.25,
                threshold=6.0,
                category="Production"
            ),
            RubricCriterion(
                name="Audio Integration",
                description="Sound design, music, and audio-visual harmony",
                weight=0.20,
                threshold=5.5,
                category="Audio"
            ),
            RubricCriterion(
                name="Pacing & Rhythm",
                description="Tempo, rhythm, and overall flow of the video",
                weight=0.15,
                threshold=5.5,
                category="Timing"
            ),
            RubricCriterion(
                name="Creative Vision",
                description="Originality and creative expression in the work",
                weight=0.15,
                threshold=5.0,
                category="Creativity"
            )
        ]
    )
    
    return [
        ai_arts_rubric,
        digital_art_rubric,
        creative_writing_rubric,
        video_content_rubric
    ]

def save_rubrics():
    """Save sample rubrics to the data directory."""
    rubrics_dir = Path("data/rubrics")
    rubrics_dir.mkdir(parents=True, exist_ok=True)
    
    rubrics = create_sample_rubrics()
    
    for rubric in rubrics:
        rubric_file = rubrics_dir / f"{rubric.id}.json"
        with rubric_file.open("w", encoding="utf-8") as f:
            json.dump(rubric.model_dump(mode='json'), f, indent=2, default=str)
        print(f"✅ Created rubric: {rubric.name}")
    
    print(f"\n🎯 Created {len(rubrics)} sample rubrics in data/rubrics/")
    print("These rubrics are ready for MVP testing!")

if __name__ == "__main__":
    save_rubrics()