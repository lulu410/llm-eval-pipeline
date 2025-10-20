# file: utils/schema.py
"""
Pydantic models for evaluation results and configuration.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class RunResult(BaseModel):
    """Result for a single evaluation run."""
    run_idx: int = Field(description="Run index (0-based)")
    label: str = Field(description="Generated label (A, B, or C)")
    latency_ms: int = Field(description="Simulated latency in milliseconds")
    hash_input: str = Field(description="Hash input used for this run")


class EvaluationResult(BaseModel):
    """Complete evaluation result."""
    timestamp_utc: str = Field(description="UTC timestamp in ISO-8601 format")
    input_text: str = Field(description="Original input text")
    input_sha256: str = Field(description="SHA256 of input text")
    config_sha256: str = Field(description="SHA256 of evaluation configuration")
    results_sha256: str = Field(description="SHA256 of this result JSON")
    
    # Configuration
    seed: int = Field(description="Random seed used")
    runs: int = Field(description="Number of evaluation runs")
    reproducibility_threshold: float = Field(description="Threshold for reproducibility pass/fail")
    variance_threshold: float = Field(description="Threshold for variance pass/fail")
    
    # Optional fields
    org_name: Optional[str] = Field(None, description="Organization name if provided")
    doi: Optional[str] = Field(None, description="DOI if provided")
    
    # Results
    run_results: List[RunResult] = Field(description="Results for each run")
    reproducibility_score: float = Field(description="Fraction of runs with majority label")
    latency_mean_ms: float = Field(description="Mean latency across runs")
    latency_stdev_ms: float = Field(description="Standard deviation of latency")
    latency_variance_ratio: float = Field(description="Coefficient of variation (stdev/mean)")
    
    # Pass/fail
    reproducibility_passed: bool = Field(description="Whether reproducibility threshold was met")
    variance_passed: bool = Field(description="Whether variance threshold was met")
    overall_passed: bool = Field(description="Whether all tests passed")


class EvaluationConfig(BaseModel):
    """Configuration for evaluation run."""
    seed: int = Field(description="Random seed")
    runs: int = Field(description="Number of runs")
    reproducibility_threshold: float = Field(description="Reproducibility threshold")
    variance_threshold: float = Field(description="Variance threshold")
    org_name: Optional[str] = Field(None, description="Organization name")
    doi: Optional[str] = Field(None, description="DOI")
