#!/usr/bin/env python3
"""
Hugging Face Space version of AI Arts Evaluation MVP
Optimized for Artiver.ai integration with modern UI
"""

import gradio as gr
import base64
import json
import uuid
import asyncio
from typing import List, Dict, Any
from pathlib import Path
import os

# Import our existing modules
from src.models import MultimodalSubmission, DynamicRubric, RubricCriterion, ModelProvider
from src.rubric_manager import RubricManager
from src.multimodal_evaluator import MultimodalEvaluator

# Initialize components
rubric_manager = RubricManager()

def get_evaluator(api_key):
    """Get evaluator with API key."""
    return MultimodalEvaluator({
        "api_key": api_key or os.getenv("GEMINI_API_KEY", "your-gemini-api-key")
    })

async def evaluate_artwork_async(image, title, api_key):
    """Evaluate artwork using Digital Art Evaluation rubric."""
    try:
        # Convert image to base64
        if image is None:
            return "Please upload an image first.", None
        
        # Convert PIL image to base64
        import io
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Get Digital Art Evaluation rubric
        rubric = rubric_manager.get_rubric("digital_art_evaluation")
        if not rubric:
            return "Digital Art Evaluation rubric not found.", None
        
        # Create submission
        submission = MultimodalSubmission(
            id=str(uuid.uuid4()),
            rubric_ids=["digital_art_evaluation"],
            media_items=[{
                "media_type": "image",
                "content": image_b64,
                "metadata": {"filename": f"{title}.png"},
                "filename": f"{title}.png"
            }],
            title=title,
            description=f"Artwork: {title}"
        )
        
        # Get evaluator with API key
        evaluator = get_evaluator(api_key)
        
        # Evaluate
        result = await evaluator.evaluate_submission_multi_rubric(
            submission, [rubric], ModelProvider.GOOGLE_GEMINI
        )
        
        # Format results
        rubric_result = result.rubric_results[0]
        
        # Create results summary
        summary = f"""
## 🎨 {title}

**Overall Score: {result.overall_average_score:.1f}/10**
**Status: {'✅ PASSED' if result.overall_passed else '❌ FAILED'}**
**Evaluation Mode: {'🤖 AI EVALUATION' if not rubric_result.fallback_reason else '⚠️ DETERMINISTIC'}**

### 📊 Detailed Scores:
"""
        
        for score in rubric_result.criterion_scores:
            summary += f"""
**{score.criterion_name}: {score.score:.1f}/10**
- {score.feedback}
- *{score.reasoning}*
"""
        
        # Create JSON export
        export_data = {
            "artwork_title": title,
            "overall_score": result.overall_average_score,
            "passed": result.overall_passed,
            "evaluation_mode": "AI" if not rubric_result.fallback_reason else "Deterministic",
            "criterion_scores": [
                {
                    "criterion": score.criterion_name,
                    "score": score.score,
                    "feedback": score.feedback,
                    "reasoning": score.reasoning
                }
                for score in rubric_result.criterion_scores
            ],
            "rubric_used": "Digital Art Evaluation",
            "evaluated_at": result.evaluated_at.isoformat()
        }
        
        return summary, json.dumps(export_data, indent=2)
        
    except Exception as e:
        return f"Error evaluating artwork: {str(e)}", None

def evaluate_artwork(image, title, api_key):
    """Wrapper to run async function."""
    return asyncio.run(evaluate_artwork_async(image, title, api_key))

# Create Gradio interface with modern design
with gr.Blocks(
    title="AI Arts Evaluation - Powered by Artiver",
    theme=gr.themes.Soft(),
    css="""
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
    }
    .artiver-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 30px;
    }
    .artiver-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 10px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .artiver-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0;
    }
    .upload-section {
        background: white;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .results-section {
        background: white;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .score-display {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .score-number {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .criterion-item {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #3498db;
    }
    .criterion-name {
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    .criterion-score {
        font-size: 1.2rem;
        font-weight: 700;
        color: #3498db;
        margin-bottom: 5px;
    }
    """
) as demo:
    
    gr.HTML("""
    <div class="artiver-header">
        <h1>🎨 AI Arts Evaluation Tool</h1>
        <p>Powered by <strong>Artiver.ai</strong> - Empowering Digital Creators Globally</p>
        <p>Evaluate your AI-generated artwork with professional criteria</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML('<div class="upload-section">')
            gr.Markdown("### 📤 Upload Your Artwork")
            
            api_key_input = gr.Textbox(
                label="Gemini API Key",
                placeholder="Enter your Gemini API key (or leave empty if set in environment)",
                type="password",
                info="Get your API key from https://makersuite.google.com/app/apikey"
            )
            
            image_input = gr.Image(
                label="Upload Image",
                type="pil",
                height=400
            )
            title_input = gr.Textbox(
                label="Artwork Title",
                placeholder="Enter your artwork title...",
                value="Untitled Artwork"
            )
            evaluate_btn = gr.Button(
                "🎯 Evaluate with AI",
                variant="primary",
                size="lg"
            )
            gr.HTML('</div>')
            
        with gr.Column(scale=1):
            gr.HTML('<div class="results-section">')
            gr.Markdown("### 📊 Evaluation Results")
            results_output = gr.Markdown()
            
            gr.Markdown("### 📥 Export Results")
            export_output = gr.JSON(
                label="JSON Export",
                visible=False
            )
            download_btn = gr.DownloadButton(
                "💾 Download Results",
                visible=False
            )
            gr.HTML('</div>')
    
    # Event handlers
    def on_evaluate(image, title, api_key):
        if image is None:
            return "Please upload an image first.", None, gr.update(visible=False), gr.update(visible=False)
        
        summary, json_data = evaluate_artwork(image, title, api_key)
        
        if json_data:
            return summary, json_data, gr.update(visible=True), gr.update(visible=True)
        else:
            return summary, None, gr.update(visible=False), gr.update(visible=False)
    
    evaluate_btn.click(
        fn=on_evaluate,
        inputs=[image_input, title_input, api_key_input],
        outputs=[results_output, export_output, gr.update(visible=True), gr.update(visible=True)]
    )
    
    gr.Markdown("""
    ---
    ### 🏆 About This Tool
    
    This AI Arts Evaluation tool uses professional criteria to assess digital artwork:
    
    - Visual Composition: Balance, harmony, and visual flow
    - Color Harmony: Effective use of color and contrast  
    - Detail & Resolution: Technical precision and quality
    - Emotional Impact: Ability to evoke emotions
    - Originality: Creative uniqueness and innovation
    
    Powered by Gemini Pro Vision AI for accurate, detailed evaluation.
    
    ---
    *This tool is integrated with [Artiver.ai](https://www.artiver.ai/) - Empowering Digital Creators Globally*
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,  # This creates a public URL
        show_error=True
    )