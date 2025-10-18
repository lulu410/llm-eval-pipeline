"""
FastAPI web interface for the enhanced LLM evaluation pipeline.
Provides REST API endpoints for dynamic rubric management, multimodal submissions,
backend model integration, and structured report generation.
"""

import json
import uuid
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .models import (
    DynamicRubric, RubricCriterion, MultimodalSubmission, MediaItem, 
    MediaType, EvaluationRequest, EvaluationResult, BatchEvaluationRequest,
    BatchEvaluationResult, ReportRequest, ReportExportFormat, ModelProvider
)
from .rubric_manager import RubricManager
from .multimodal_evaluator import MultimodalEvaluator
from .report_generator import ReportGenerator

# Initialize FastAPI app
app = FastAPI(
    title="LLM Evaluation Pipeline API",
    description="Enhanced multimodal LLM evaluation with dynamic rubrics and backend model integration",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
rubric_manager = RubricManager()
report_generator = ReportGenerator()

# Global model configuration (in production, this should come from environment variables)
MODEL_CONFIG = {
    "openai": {"api_key": "your-openai-api-key"},
    "google_gemini": {"api_key": "your-gemini-api-key"}
}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"message": "LLM Evaluation Pipeline API v2.0.0", "status": "healthy"}


# Rubric Management Endpoints

@app.post("/rubrics", response_model=DynamicRubric)
async def create_rubric(
    rubric_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    criteria_json: str = Form(...)  # JSON string of criteria list
):
    """Create a new dynamic rubric."""
    try:
        criteria_data = json.loads(criteria_json)
        criteria = [RubricCriterion(**criterion) for criterion in criteria_data]
        
        rubric = rubric_manager.create_rubric(rubric_id, name, description, criteria)
        
        if not rubric_manager.validate_rubric_weights(rubric_id):
            raise HTTPException(
                status_code=400, 
                detail="Invalid rubric: criterion weights must sum to 1.0"
            )
        
        return rubric
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid criteria JSON")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/rubrics", response_model=List[DynamicRubric])
async def list_rubrics():
    """List all available rubrics."""
    return rubric_manager.list_rubrics()


@app.get("/rubrics/{rubric_id}", response_model=DynamicRubric)
async def get_rubric(rubric_id: str):
    """Get a specific rubric by ID."""
    rubric = rubric_manager.get_rubric(rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rubric


@app.put("/rubrics/{rubric_id}", response_model=DynamicRubric)
async def update_rubric(
    rubric_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    criteria_json: Optional[str] = Form(None)
):
    """Update an existing rubric."""
    criteria = None
    if criteria_json:
        try:
            criteria_data = json.loads(criteria_json)
            criteria = [RubricCriterion(**criterion) for criterion in criteria_data]
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid criteria JSON")
    
    try:
        rubric = rubric_manager.update_rubric(rubric_id, name, description, criteria)
        
        if not rubric_manager.validate_rubric_weights(rubric_id):
            raise HTTPException(
                status_code=400, 
                detail="Invalid rubric: criterion weights must sum to 1.0"
            )
        
        return rubric
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/rubrics/{rubric_id}")
async def delete_rubric(rubric_id: str):
    """Delete a rubric."""
    success = rubric_manager.delete_rubric(rubric_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return {"message": "Rubric deleted successfully"}


@app.get("/rubrics/{rubric_id}/export")
async def export_rubric(rubric_id: str, format: str = "json"):
    """Export a rubric in specified format."""
    try:
        content = rubric_manager.export_rubric(rubric_id, format)
        if format == "json":
            return JSONResponse(content=json.loads(content))
        else:
            return {"content": content, "format": format}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Multimodal Submission Endpoints

@app.post("/submissions", response_model=MultimodalSubmission)
async def create_submission(
    rubric_id: str = Form(...),
    files: List[UploadFile] = File(...),
    metadata_json: str = Form("{}")
):
    """Create a multimodal submission with uploaded files."""
    try:
        metadata = json.loads(metadata_json)
        submission_id = str(uuid.uuid4())
        
        media_items = []
        
        for file in files:
            # Determine media type from file extension
            media_type = MediaType.TEXT
            if file.content_type and file.content_type.startswith("image/"):
                media_type = MediaType.IMAGE
            elif file.content_type and file.content_type.startswith("video/"):
                media_type = MediaType.VIDEO
            elif file.content_type and file.content_type.startswith("audio/"):
                media_type = MediaType.AUDIO
            
            # Read file content and encode as base64
            content = await file.read()
            base64_content = base64.b64encode(content).decode('utf-8')
            
            if media_type == MediaType.IMAGE:
                base64_content = f"data:{file.content_type};base64,{base64_content}"
            
            media_item = MediaItem(
                media_type=media_type,
                content=base64_content,
                filename=file.filename,
                metadata={
                    "content_type": file.content_type,
                    "size": len(content)
                }
            )
            media_items.append(media_item)
        
        # Add text content if provided separately
        text_content = metadata.get("text_content", "")
        if text_content:
            text_item = MediaItem(
                media_type=MediaType.TEXT,
                content=text_content,
                metadata=metadata.get("text_metadata", {})
            )
            media_items.append(text_item)
        
        submission = MultimodalSubmission(
            id=submission_id,
            rubric_id=rubric_id,
            media_items=media_items
        )
        
        return submission
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Evaluation Endpoints

@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate_submission(request: EvaluationRequest):
    """Evaluate a single multimodal submission."""
    # Verify rubric exists
    rubric = rubric_manager.get_rubric(request.submission.rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    
    # Initialize evaluator with model config
    base_config = MODEL_CONFIG.get(request.model_provider.value, {})
    model_config = {**base_config, **request.config}
    evaluator = MultimodalEvaluator(model_config)
    
    try:
        result = await evaluator.evaluate_submission(
            request.submission, 
            rubric, 
            request.model_provider
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/evaluate/batch", response_model=BatchEvaluationResult)
async def evaluate_batch(request: BatchEvaluationRequest):
    """Evaluate multiple submissions in batch."""
    batch_id = request.batch_id or str(uuid.uuid4())
    
    # Initialize evaluator
    base_config = MODEL_CONFIG.get(request.model_provider.value, {})
    model_config = {**base_config, **request.config}
    evaluator = MultimodalEvaluator(model_config)
    
    results = []
    
    for submission in request.submissions:
        # Verify rubric exists for each submission
        rubric = rubric_manager.get_rubric(submission.rubric_id)
        if not rubric:
            raise HTTPException(
                status_code=404, 
                detail=f"Rubric not found for submission {submission.id}"
            )
        
        try:
            result = await evaluator.evaluate_submission(
                submission, 
                rubric, 
                request.model_provider
            )
            results.append(result)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Batch evaluation failed for submission {submission.id}: {str(e)}"
            )
    
    batch_result = BatchEvaluationResult(
        batch_id=batch_id,
        submission_results=results,
        batch_metadata={
            "total_submissions": len(request.submissions),
            "model_provider": request.model_provider.value,
            "evaluation_timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return batch_result


# Report Generation Endpoints

@app.post("/reports/generate")
async def generate_report(request: ReportRequest):
    """Generate structured evaluation report."""
    try:
        report_content = await report_generator.generate_report(request)
        
        # Save report to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_report_{timestamp}"
        file_path = report_generator.save_report(report_content, filename, request.format)
        
        return {
            "message": "Report generated successfully",
            "file_path": str(file_path),
            "content_type": request.format.value,
            "content": report_content if request.format == ReportExportFormat.JSON else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/reports/{filename}")
async def download_report(filename: str):
    """Download a generated report file."""
    file_path = report_generator.output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(file_path)


# Statistics and Analytics

@app.get("/stats")
async def get_statistics():
    """Get pipeline statistics and health information."""
    rubrics = rubric_manager.list_rubrics()
    
    return {
        "total_rubrics": len(rubrics),
        "pipeline_version": "2.0.0",
        "supported_models": [provider.value for provider in ModelProvider],
        "supported_media_types": [media_type.value for media_type in MediaType],
        "supported_export_formats": [fmt.value for fmt in ReportExportFormat]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
