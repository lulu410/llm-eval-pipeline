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
    ModelProvider, DynamicRubric, MediaType, MultiRubricEvaluationResult
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
            config_sha256=config_sha256,
            fallback_reason=result.get("fallback_reason")
        )
    
    async def evaluate_submission_multi_rubric(
        self, 
        submission: MultimodalSubmission, 
        rubrics: List[DynamicRubric],
        model_provider: ModelProvider
    ) -> MultiRubricEvaluationResult:
        """Evaluate a submission against multiple rubrics."""
        start_time = time.time()
        rubric_results = []
        
        # Evaluate against each rubric
        for rubric in rubrics:
            result = await self.evaluate_submission(submission, rubric, model_provider)
            rubric_results.append(result)
        
        # Calculate overall statistics
        overall_scores = [result.overall_score for result in rubric_results]
        overall_average_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
        overall_passed = all(result.passed for result in rubric_results)
        total_processing_time = int((time.time() - start_time) * 1000)
        
        return MultiRubricEvaluationResult(
            submission_id=submission.id,
            submission_title=submission.title,
            submission_description=submission.description,
            rubric_results=rubric_results,
            overall_average_score=overall_average_score,
            overall_passed=overall_passed,
            total_processing_time_ms=total_processing_time
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
        # Check if API key is configured
        api_key = self.model_config.get("api_key")
        if not api_key or api_key == "your-openai-api-key":
            print("OpenAI API key not configured. Falling back to deterministic evaluation.")
            result = await self._evaluate_deterministic(submission, rubric)
            # Update the result to indicate fallback
            for score in result["criterion_scores"]:
                score.feedback = f"No OpenAI API key configured. {score.feedback}"
            result["fallback_reason"] = "openai_api_key_missing"
            return result
            
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
                model="gpt-4o",  # Updated to use the latest GPT-4 model that supports vision
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
            result = await self._evaluate_deterministic(submission, rubric)
            # Update the result to indicate fallback
            for score in result["criterion_scores"]:
                score.feedback = f"OpenAI API error: {str(e)[:100]}... {score.feedback}"
            result["fallback_reason"] = "openai_api_error"
            return result
    
    async def _evaluate_gemini(
        self, 
        submission: MultimodalSubmission, 
        rubric: DynamicRubric
    ) -> Dict[str, Any]:
        """Evaluate using Google Gemini Pro Vision."""
        # Check if API key is configured
        api_key = self.model_config.get("api_key")
        if not api_key or api_key == "your-gemini-api-key":
            print("Gemini API key not configured. Falling back to deterministic evaluation.")
            result = await self._evaluate_deterministic(submission, rubric)
            # Update the result to indicate fallback
            for score in result["criterion_scores"]:
                score.feedback = f"No Gemini API key configured. {score.feedback}"
            result["fallback_reason"] = "gemini_api_key_missing"
            return result
            
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Prepare the prompt
            prompt = f"""You are an expert digital art evaluator. Please evaluate this submission using the following rubric:

Rubric: {rubric.name}
Description: {rubric.description}

Criteria:
{self._format_criteria_for_prompt(rubric.criteria)}

IMPORTANT: For each criterion, provide:
1. A score from 0-10 (be specific, not just 5.0)
2. BRIEF reasoning (max 20 words) explaining WHY you gave this score
3. Constructive feedback for improvement

Format your response EXACTLY as follows:
{chr(10).join([f"{criterion.name}: X.X/10{chr(10)}REASONING: [Brief explanation in max 20 words]{chr(10)}FEEDBACK: [Specific suggestions]{chr(10)}" for criterion in rubric.criteria])}

Be concise but insightful. Focus on the most important aspects of each criterion."""

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
            result = await self._evaluate_deterministic(submission, rubric)
            # Update the result to indicate fallback
            for score in result["criterion_scores"]:
                score.feedback = f"Gemini API error: {str(e)[:100]}... {score.feedback}"
            result["fallback_reason"] = "gemini_api_error"
            return result
    
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
        criterion_scores = []
        import re
        
        for criterion in rubric.criteria:
            # Look for detailed score format: CRITERION_NAME: X.X/10
            pattern = rf"{re.escape(criterion.name)}:\s*(\d+(?:\.\d+)?)/10"
            match = re.search(pattern, response, re.IGNORECASE)
            
            if match:
                score = float(match.group(1))
                
                # Extract reasoning and feedback
                reasoning_pattern = rf"{re.escape(criterion.name)}.*?REASONING:\s*([^\n]+(?:\n(?!FEEDBACK:)[^\n]+)*)"
                reasoning_match = re.search(reasoning_pattern, response, re.IGNORECASE | re.DOTALL)
                
                feedback_pattern = rf"{re.escape(criterion.name)}.*?FEEDBACK:\s*([^\n]+(?:\n(?!CRITERION|$)[^\n]+)*)"
                feedback_match = re.search(feedback_pattern, response, re.IGNORECASE | re.DOTALL)
                
                reasoning = reasoning_match.group(1).strip() if reasoning_match else f"AI evaluation based on {criterion.name}"
                feedback = feedback_match.group(1).strip() if feedback_match else f"AI analysis of {criterion.name}"
                
            else:
                # Fallback: look for simple score format
                simple_pattern = rf"{re.escape(criterion.name)}.*?(\d+(?:\.\d+)?)/10"
                simple_match = re.search(simple_pattern, response, re.IGNORECASE | re.DOTALL)
                
                if simple_match:
                    score = float(simple_match.group(1))
                    reasoning = f"AI evaluation based on {criterion.name}"
                    feedback = f"Score: {score:.1f}/10"
                else:
                    # Ultimate fallback
                    score = 5.0
                    reasoning = f"No specific score found for {criterion.name}, using default"
                    feedback = f"Default score: {score:.1f}/10"
            
            passed = score >= criterion.threshold
            
            criterion_scores.append(CriterionScore(
                criterion_name=criterion.name,
                score=score,
                feedback=feedback,
                reasoning=reasoning
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
