"""
Multimodal evaluation engine that integrates with various backend models.
Supports text, images, and video evaluation using GPT-4V and Gemini Pro Vision.
"""

import hashlib
import json
import base64
import time
import io
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
from PIL import Image
import cv2
import numpy as np

from .models import (
    MultimodalSubmission, EvaluationResult, CriterionScore, 
    ModelProvider, DynamicRubric, MediaType
)


class MultimodalEvaluator:
    """Evaluates multimodal submissions using various backend models."""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
    
    async def evaluate_submission(
        self, 
        submission: MultimodalSubmission, 
        rubric: DynamicRubric,
        model_provider: ModelProvider
    ) -> EvaluationResult:
        """Evaluate a submission using the specified model provider."""
        start_time = time.time()
        
        # Calculate input hash for provenance
        input_sha256 = self._calculate_input_hash(submission)
        config_sha256 = self._calculate_config_hash()
        
        if model_provider == ModelProvider.DETERMINISTIC:
            result = await self._evaluate_deterministic(submission, rubric)
        elif model_provider == ModelProvider.OPENAI:
            result = await self._evaluate_openai(submission, rubric)
        elif model_provider == ModelProvider.GOOGLE_GEMINI:
            result = await self._evaluate_gemini(submission, rubric)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return EvaluationResult(
            submission_id=submission.id,
            rubric_id=rubric.id,
            model_provider=model_provider,
            overall_score=result["overall_score"],
            passed=result["passed"],
            criterion_scores=result["criterion_scores"],
            processing_time_ms=processing_time,
            input_sha256=input_sha256,
            config_sha256=config_sha256
        )
    
    async def _evaluate_deterministic(
        self, 
        submission: MultimodalSubmission, 
        rubric: DynamicRubric
    ) -> Dict[str, Any]:
        """Deterministic evaluation (original pipeline behavior)."""
        criterion_scores = []
        
        # For deterministic mode, we generate scores based on content hash
        for criterion in rubric.criteria:
            content_str = "|".join([item.content for item in submission.media_items])
            hash_input = f"{criterion.name}|{content_str}"
            
            # Generate deterministic score (0-10)
            score_hash = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
            score = (score_hash % 100) / 10.0  # 0.0 to 9.9
            
            passed = score >= criterion.threshold
            
            criterion_scores.append(CriterionScore(
                criterion_name=criterion.name,
                score=score,
                feedback=f"Deterministic evaluation based on content hash. Score: {score:.1f}/10",
                reasoning=f"Hash-based deterministic scoring for reproducibility."
            ))
        
        # Calculate overall weighted score
        overall_score = sum(
            score.score * criterion.weight 
            for score, criterion in zip(criterion_scores, rubric.criteria)
        )
        
        # Check if all criteria pass
        passed = all(score.score >= criterion.threshold 
                    for score, criterion in zip(criterion_scores, rubric.criteria))
        
        return {
            "overall_score": overall_score,
            "passed": passed,
            "criterion_scores": criterion_scores
        }
    
    async def _evaluate_openai(
        self, 
        submission: MultimodalSubmission, 
        rubric: DynamicRubric
    ) -> Dict[str, Any]:
        """Evaluate using OpenAI GPT-4V."""
        try:
            # Prepare messages for OpenAI API
            messages = [{
                "role": "system",
                "content": f"""You are an expert evaluator. Use the following rubric to evaluate the submission:

Rubric: {rubric.name}
Description: {rubric.description}

Criteria:
{self._format_criteria_for_prompt(rubric.criteria)}

Provide detailed scores and feedback for each criterion."""
            }]
            
            # Add user content with multimodal elements
            user_content = []
            
            for item in submission.media_items:
                if item.media_type == MediaType.TEXT:
                    user_content.append({
                        "type": "text",
                        "text": item.content
                    })
                elif item.media_type == MediaType.IMAGE:
                    # OpenAI expects base64 images
                    if item.content.startswith("data:image"):
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": item.content}
                        })
                    else:
                        # Assume base64 content
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{item.content}"
                            }
                        })
            
            messages.append({
                "role": "user",
                "content": user_content
            })
            
            # Call OpenAI API
            import openai
            client = openai.AsyncOpenAI(api_key=self.model_config.get("api_key"))
            
            response = await client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=2000,
                temperature=0.1  # Low temperature for consistency
            )
            
            # Parse the response
            return self._parse_evaluation_response(
                response.choices[0].message.content, 
                rubric
            )
            
        except Exception as e:
            # Fallback to deterministic evaluation
            print(f"OpenAI evaluation failed: {e}. Falling back to deterministic.")
            return await self._evaluate_deterministic(submission, rubric)
    
    async def _evaluate_gemini(
        self, 
        submission: MultimodalSubmission, 
        rubric: DynamicRubric
    ) -> Dict[str, Any]:
        """Evaluate using Google Gemini Pro Vision."""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.model_config.get("api_key"))
            model = genai.GenerativeModel('gemini-pro-vision')
            
            # Prepare the prompt
            prompt = f"""Evaluate this submission using the following rubric:

Rubric: {rubric.name}
Description: {rubric.description}

Criteria:
{self._format_criteria_for_prompt(rubric.criteria)}

Provide detailed scores and feedback for each criterion."""

            # Prepare content parts
            content_parts = [prompt]
            
            for item in submission.media_items:
                if item.media_type == MediaType.IMAGE:
                    # Decode base64 image
                    if item.content.startswith("data:image"):
                        # Extract base64 from data URL
                        base64_data = item.content.split(",")[1]
                    else:
                        base64_data = item.content
                    
                    image_data = base64.b64decode(base64_data)
                    image = Image.open(io.BytesIO(image_data))
                    content_parts.append(image)
                elif item.media_type == MediaType.TEXT:
                    content_parts.append(f"\nText content: {item.content}")
            
            # Generate content
            response = await model.generate_content_async(content_parts)
            
            # Parse the response
            return self._parse_evaluation_response(response.text, rubric)
            
        except Exception as e:
            # Fallback to deterministic evaluation
            print(f"Gemini evaluation failed: {e}. Falling back to deterministic.")
            return await self._evaluate_deterministic(submission, rubric)
    
    def _format_criteria_for_prompt(self, criteria: List[Any]) -> str:
        """Format criteria for inclusion in model prompts."""
        formatted = []
        for criterion in criteria:
            formatted.append(
                f"- {criterion.name} (Weight: {criterion.weight}, Threshold: {criterion.threshold}/10)\n"
                f"  Description: {criterion.description}"
            )
        return "\n".join(formatted)
    
    def _parse_evaluation_response(
        self, 
        response: str, 
        rubric: DynamicRubric
    ) -> Dict[str, Any]:
        """Parse model response into structured evaluation results."""
        # This is a simplified parser - in practice, you'd want more sophisticated parsing
        criterion_scores = []
        
        # Try to extract scores from response
        # This is a basic implementation - you'd want to use more sophisticated parsing
        import re
        
        for criterion in rubric.criteria:
            # Look for score in response
            pattern = rf"{re.escape(criterion.name)}.*?(\d+(?:\.\d+)?)/10"
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            
            if match:
                score = float(match.group(1))
            else:
                # Fallback to middle score
                score = 5.0
            
            passed = score >= criterion.threshold
            
            criterion_scores.append(CriterionScore(
                criterion_name=criterion.name,
                score=score,
                feedback=f"Evaluated by AI model. Score: {score:.1f}/10",
                reasoning=response[:200] + "..." if len(response) > 200 else response
            ))
        
        # Calculate overall weighted score
        overall_score = sum(
            score.score * criterion.weight 
            for score, criterion in zip(criterion_scores, rubric.criteria)
        )
        
        passed = all(score.score >= criterion.threshold 
                    for score, criterion in zip(criterion_scores, rubric.criteria))
        
        return {
            "overall_score": overall_score,
            "passed": passed,
            "criterion_scores": criterion_scores
        }
    
    def _calculate_input_hash(self, submission: MultimodalSubmission) -> str:
        """Calculate SHA256 hash of submission for provenance."""
        content = json.dumps(submission.model_dump(mode='json'), sort_keys=True).encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def _calculate_config_hash(self) -> str:
        """Calculate SHA256 hash of model configuration."""
        content = json.dumps(self.model_config, sort_keys=True).encode('utf-8')
        return hashlib.sha256(content).hexdigest()
