"""
Data models for the enhanced LLM evaluation pipeline.
Supports dynamic rubrics, multimodal submissions, and structured reports.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import base64
from datetime import datetime


class MediaType(str, Enum):
    """Supported media types for multimodal submissions."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class RubricCriterion(BaseModel):
    """Individual criterion within a rubric."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(description="Name of the criterion")
    description: str = Field(description="Detailed description of what is being evaluated")
    weight: float = Field(ge=0, le=1, description="Weight of this criterion (0-1)")
    threshold: float = Field(ge=0, le=10, description="Passing threshold (0-10)")
    category: str = Field(description="Category this criterion belongs to")


class DynamicRubric(BaseModel):
    """Dynamic rubric definition with configurable criteria."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str = Field(description="Unique identifier for the rubric")
    name: str = Field(description="Human-readable name for the rubric")
    description: str = Field(description="Description of what this rubric evaluates")
    criteria: List[RubricCriterion] = Field(description="List of evaluation criteria")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MediaItem(BaseModel):
    """Individual media item in a multimodal submission."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    media_type: MediaType = Field(description="Type of media")
    content: str = Field(description="Base64 encoded content or text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata like caption, order, duration")
    filename: Optional[str] = Field(None, description="Original filename if applicable")


class MultimodalSubmission(BaseModel):
    """Submission that can contain multiple media types."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str = Field(description="Unique identifier for the submission")
    rubric_ids: List[str] = Field(description="List of rubric IDs to use for evaluation")
    media_items: List[MediaItem] = Field(description="List of media items in the submission")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    batch_id: Optional[str] = Field(None, description="Batch ID for batch processing")
    title: Optional[str] = Field(None, description="Title of the submission")
    description: Optional[str] = Field(None, description="Description of the submission")


class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    GOOGLE_GEMINI = "google_gemini"
    DETERMINISTIC = "deterministic"  # Original deterministic mode


class EvaluationRequest(BaseModel):
    """Request to evaluate a submission."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    submission: MultimodalSubmission = Field(description="Submission to evaluate")
    model_provider: ModelProvider = Field(description="Model provider to use")
    config: Dict[str, Any] = Field(default_factory=dict, description="Model-specific configuration")


class CriterionScore(BaseModel):
    """Score for an individual criterion."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    criterion_name: str = Field(description="Name of the criterion")
    score: float = Field(ge=0, le=10, description="Score for this criterion (0-10)")
    feedback: str = Field(description="Detailed feedback for this criterion")
    reasoning: str = Field(description="Reasoning behind the score")


class EvaluationResult(BaseModel):
    """Complete evaluation result for a submission."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    submission_id: str = Field(description="ID of the evaluated submission")
    rubric_id: str = Field(description="ID of the rubric used")
    model_provider: ModelProvider = Field(description="Model provider used")
    overall_score: float = Field(ge=0, le=10, description="Overall weighted score")
    passed: bool = Field(description="Whether the submission passed all thresholds")
    criterion_scores: List[CriterionScore] = Field(description="Scores for each criterion")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = Field(description="Time taken to evaluate in milliseconds")
    input_sha256: str = Field(description="SHA256 hash of input for provenance")
    config_sha256: str = Field(description="SHA256 hash of config for provenance")
    fallback_reason: Optional[str] = Field(None, description="Reason for fallback to deterministic evaluation")


class MultiRubricEvaluationResult(BaseModel):
    """Results for evaluating a submission against multiple rubrics."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    submission_id: str = Field(description="ID of the evaluated submission")
    submission_title: Optional[str] = Field(None, description="Title of the submission")
    submission_description: Optional[str] = Field(None, description="Description of the submission")
    rubric_results: List[EvaluationResult] = Field(description="Results for each rubric")
    overall_average_score: float = Field(description="Average score across all rubrics")
    overall_passed: bool = Field(description="Whether submission passed all rubrics")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    total_processing_time_ms: int = Field(description="Total time for all evaluations")


class BatchEvaluationRequest(BaseModel):
    """Request to evaluate multiple submissions in batch."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    submissions: List[MultimodalSubmission] = Field(description="List of submissions to evaluate")
    model_provider: ModelProvider = Field(description="Model provider to use")
    config: Dict[str, Any] = Field(default_factory=dict, description="Model-specific configuration")
    batch_id: Optional[str] = Field(None, description="Optional batch identifier")


class BatchEvaluationResult(BaseModel):
    """Results for batch evaluation."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    batch_id: str = Field(description="Batch identifier")
    submission_results: List[MultiRubricEvaluationResult] = Field(description="Results for each submission")
    batch_metadata: Dict[str, Any] = Field(default_factory=dict, description="Batch-level metadata")
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    total_submissions: int = Field(description="Total number of submissions processed")
    successful_evaluations: int = Field(description="Number of successful evaluations")
    failed_evaluations: int = Field(description="Number of failed evaluations")


class ReportExportFormat(str, Enum):
    """Supported export formats for evaluation reports."""
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"


class ReportRequest(BaseModel):
    """Request to generate evaluation report."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    evaluation_results: List[EvaluationResult] = Field(description="Results to include in report")
    rubric: DynamicRubric = Field(description="Rubric used for evaluation")
    format: ReportExportFormat = Field(description="Export format for the report")
    include_metadata: bool = Field(True, description="Whether to include provenance metadata")


class SystemInfo(BaseModel):
    """System information for provenance tracking."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    python_version: str = Field(description="Python version")
    platform: str = Field(description="Platform information")
    pipeline_version: str = Field(description="Pipeline version")
