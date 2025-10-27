"""
MVP API for AI Arts Competition style evaluation.
Focuses on batch processing with Gemini-only mode and multi-rubric support.
"""

import os
import uuid
import base64
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .models import (
    MultimodalSubmission, DynamicRubric, RubricCriterion, 
    ModelProvider, MultiRubricEvaluationResult, BatchEvaluationResult, CriterionScore
)
from .rubric_manager import RubricManager
from .multimodal_evaluator import MultimodalEvaluator

# MVP Configuration - Gemini only for all media processing
MVP_MODEL_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY", "your-gemini-api-key")
}

app = FastAPI(title="LLM Evaluation Pipeline MVP", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
rubric_manager = RubricManager()
evaluator = MultimodalEvaluator(MVP_MODEL_CONFIG)

# Create data directories
Path("data/mvp_submissions").mkdir(parents=True, exist_ok=True)
Path("data/mvp_results").mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def mvp_dashboard():
    """MVP Dashboard - AI Arts Competition style interface."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Arts Evaluation MVP</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            /* Modern Art Platform Design */
            :root {
                --primary-color: #2c3e50;
                --secondary-color: #34495e;
                --accent-color: #3498db;
                --success-color: #27ae60;
                --warning-color: #f39c12;
                --danger-color: #e74c3c;
                --light-gray: #ecf0f1;
                --dark-gray: #7f8c8d;
                --white: #ffffff;
                --shadow: 0 2px 20px rgba(0,0,0,0.1);
                --shadow-hover: 0 8px 30px rgba(0,0,0,0.15);
                --border-radius: 12px;
                --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }
            
            .container-fluid {
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .header-card {
                background: var(--white);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                padding: 3rem;
                text-align: center;
                margin-bottom: 3rem;
                border: none;
            }
            
            .header-card h1 {
                font-size: 3rem;
                font-weight: 700;
                color: var(--primary-color);
                margin-bottom: 1rem;
                letter-spacing: -0.02em;
            }
            
            .header-card p {
                font-size: 1.2rem;
                color: var(--dark-gray);
                margin-bottom: 0;
                font-weight: 400;
            }
            
            .upload-card {
                background: var(--white);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                border: none;
                overflow: hidden;
                transition: var(--transition);
            }
            
            .upload-card:hover {
                box-shadow: var(--shadow-hover);
                transform: translateY(-2px);
            }
            
            .upload-area {
                border: 3px dashed var(--accent-color);
                border-radius: var(--border-radius);
                padding: 3rem;
                text-align: center;
                background: linear-gradient(135deg, #f8f9ff 0%, #e8f4fd 100%);
                transition: var(--transition);
                position: relative;
                overflow: hidden;
            }
            
            .upload-area::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(45deg, transparent 30%, rgba(52, 152, 219, 0.1) 50%, transparent 70%);
                transform: translateX(-100%);
                transition: transform 0.6s;
            }
            
            .upload-area:hover::before {
                transform: translateX(100%);
            }
            
            .upload-area:hover {
                border-color: var(--success-color);
                background: linear-gradient(135deg, #f0fff4 0%, #e8f8f5 100%);
                transform: scale(1.02);
            }
            
            .upload-area.dragover {
                border-color: var(--success-color);
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                transform: scale(1.05);
            }
            
            .upload-icon {
                font-size: 4rem;
                color: var(--accent-color);
                margin-bottom: 1.5rem;
                display: block;
            }
            
            .upload-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--primary-color);
                margin-bottom: 0.5rem;
            }
            
            .upload-subtitle {
                color: var(--dark-gray);
                font-size: 1rem;
                margin-bottom: 2rem;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, var(--accent-color) 0%, #2980b9 100%);
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 1rem;
                transition: var(--transition);
                box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
                background: linear-gradient(135deg, #2980b9 0%, var(--accent-color) 100%);
            }
            
            .btn-success {
                background: linear-gradient(135deg, var(--success-color) 0%, #229954 100%);
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-weight: 600;
                font-size: 1.1rem;
                transition: var(--transition);
                box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
            }
            
            .btn-success:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
            }
            
            .btn-outline-secondary {
                border: 2px solid var(--dark-gray);
                color: var(--dark-gray);
                background: transparent;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                transition: var(--transition);
            }
            
            .btn-outline-secondary:hover {
                background: var(--dark-gray);
                color: var(--white);
                transform: translateY(-1px);
            }
            
            .results-card {
                background: var(--white);
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                border: none;
                overflow: hidden;
            }
            
            .score-display {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: var(--white);
                padding: 2rem;
                text-align: center;
                border-radius: var(--border-radius) var(--border-radius) 0 0;
            }
            
            .score-number {
                font-size: 4rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            .score-label {
                font-size: 1.2rem;
                opacity: 0.9;
                font-weight: 500;
            }
            
            .status-badge {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .status-passed {
                background: linear-gradient(135deg, var(--success-color) 0%, #229954 100%);
                color: var(--white);
            }
            
            .status-failed {
                background: linear-gradient(135deg, var(--danger-color) 0%, #c0392b 100%);
                color: var(--white);
            }
            
            .status-ai {
                background: linear-gradient(135deg, var(--accent-color) 0%, #2980b9 100%);
                color: var(--white);
            }
            
            .status-deterministic {
                background: linear-gradient(135deg, var(--warning-color) 0%, #e67e22 100%);
                color: var(--white);
            }
            
            .criterion-item {
                background: var(--light-gray);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                border-left: 4px solid var(--accent-color);
                transition: var(--transition);
            }
            
            .criterion-item:hover {
                transform: translateX(4px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            
            .criterion-name {
                font-size: 1.1rem;
                font-weight: 600;
                color: var(--primary-color);
                margin-bottom: 0.5rem;
            }
            
            .criterion-score {
                font-size: 1.3rem;
                font-weight: 700;
                color: var(--accent-color);
                margin-bottom: 0.5rem;
            }
            
            .criterion-feedback {
                color: var(--dark-gray);
                font-size: 0.95rem;
                line-height: 1.5;
                margin-bottom: 0.5rem;
            }
            
            .criterion-reasoning {
                color: var(--secondary-color);
                font-size: 0.9rem;
                font-style: italic;
                line-height: 1.4;
            }
            
            .score-interpretation {
                background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%);
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 2rem;
                border: 1px solid rgba(52, 152, 219, 0.2);
            }
            
            .score-range {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 0.85rem;
                font-weight: 600;
                margin-right: 0.5rem;
                margin-bottom: 0.5rem;
            }
            
            .score-range-label {
                margin-left: 0.5rem;
                margin-right: 1rem;
                font-weight: 500;
                color: var(--dark-gray);
            }
            
            .range-excellent { background: var(--success-color); color: var(--white); }
            .range-good { background: var(--accent-color); color: var(--white); }
            .range-fair { background: var(--warning-color); color: var(--white); }
            .range-poor { background: var(--danger-color); color: var(--white); }
            
            .artwork-preview {
                border-radius: var(--border-radius);
                overflow: hidden;
                box-shadow: var(--shadow);
                transition: var(--transition);
            }
            
            .artwork-preview:hover {
                transform: scale(1.02);
                box-shadow: var(--shadow-hover);
            }
            
            .artwork-preview img,
            .artwork-preview video {
                width: 100%;
                height: auto;
                display: block;
            }
            
            .file-info {
                background: var(--light-gray);
                padding: 1rem;
                border-radius: 0 0 var(--border-radius) var(--border-radius);
                text-align: center;
            }
            
            .file-name {
                font-weight: 600;
                color: var(--primary-color);
                margin-bottom: 0.25rem;
            }
            
            .file-status {
                color: var(--success-color);
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .container-fluid {
                    padding: 1rem;
                }
                
                .header-card {
                    padding: 2rem;
                }
                
                .header-card h1 {
                    font-size: 2rem;
                }
                
                .upload-area {
                    padding: 2rem;
                }
                
                .score-number {
                    font-size: 3rem;
                }
            }
            
            /* Loading Animation */
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255,255,255,.3);
                border-radius: 50%;
                border-top-color: #fff;
                animation: spin 1s ease-in-out infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            /* Modal Styles */
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                backdrop-filter: blur(5px);
            }
            
            .modal-content {
                background: var(--white);
                border-radius: var(--border-radius);
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 90vw;
                max-height: 90vh;
                overflow-y: auto;
                animation: modalSlideIn 0.3s ease-out;
            }
            
            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: scale(0.9) translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
            }
            
            .modal-header {
                padding: 2rem 2rem 1rem;
                border-bottom: 1px solid var(--light-gray);
                position: relative;
            }
            
            .modal-close {
                position: absolute;
                top: 1rem;
                right: 1rem;
                background: none;
                border: none;
                font-size: 1.5rem;
                color: var(--dark-gray);
                cursor: pointer;
                padding: 0.5rem;
                border-radius: 50%;
                transition: var(--transition);
            }
            
            .modal-close:hover {
                background: var(--light-gray);
                color: var(--primary-color);
            }
            
            .modal-body {
                padding: 2rem;
            }
        </style>
    </head>
    <body class="bg-light">
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <div class="header-card">
                        <h1>
                            <i class="fas fa-palette"></i>
                            AI Arts Evaluation
                        </h1>
                        <p>
                            Professional artwork assessment powered by AI
                        </p>
                    </div>
                </div>
            </div>

            <!-- Upload Section -->
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="upload-card">
                        <div class="upload-area" id="uploadArea">
                            <div id="uploadContent">
                                <i class="fas fa-cloud-upload-alt upload-icon"></i>
                                <h5 class="upload-title">Upload Your Artwork</h5>
                                <p class="upload-subtitle">Drag & drop or click to select</p>
                                <input type="file" id="fileInput" accept="image/*,video/*" style="display: none;">
                                <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                                    <i class="fas fa-plus"></i> Select File
                                </button>
                            </div>
                        </div>
                        <div class="file-info" id="fileActions" style="display: none;">
                            <div class="file-name" id="fileName"></div>
                            <div class="file-status">Ready for evaluation</div>
                            <div class="mt-3">
                                <button class="btn btn-outline-secondary btn-sm me-2" onclick="document.getElementById('fileInput').click()">
                                    <i class="fas fa-edit"></i> Update File
                                </button>
                                <button class="btn btn-success" id="processEvaluation">
                                    <i class="fas fa-magic"></i> Evaluate with AI
                                </button>
                                <button class="btn btn-outline-primary btn-sm ms-2" id="viewResults" onclick="openModal()" style="display: none;">
                                    <i class="fas fa-chart-bar"></i> View Results
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Modal for Results -->
            <div class="modal-overlay" id="resultsModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3><i class="fas fa-chart-bar"></i> Evaluation Results</h3>
                        <button class="modal-close" onclick="closeModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body" id="modalResultsContainer">
                        <!-- Results will be displayed here -->
                    </div>
                </div>
            </div>

        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let selectedFile = null;
            let evaluationResult = null;

            // File upload handling
            document.getElementById('fileInput').addEventListener('change', handleFile);
            document.getElementById('uploadArea').addEventListener('click', () => {
                document.getElementById('fileInput').click();
            });

            // Drag and drop
            const uploadArea = document.getElementById('uploadArea');
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                handleFile({ target: { files: e.dataTransfer.files } });
            });

            function handleFile(event) {
                const file = event.target.files[0];
                if (file) {
                    selectedFile = file;
                    showPreview(file);
                    updateProcessButton();
                }
            }

            function showPreview(file) {
                const uploadContent = document.getElementById('uploadContent');
                const fileActions = document.getElementById('fileActions');
                const fileName = document.getElementById('fileName');
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    if (file.type.startsWith('image/')) {
                        uploadContent.innerHTML = `
                            <div class="artwork-preview">
                                <img src="${e.target.result}" class="img-fluid">
                            </div>
                        `;
                    } else if (file.type.startsWith('video/')) {
                        uploadContent.innerHTML = `
                            <div class="artwork-preview">
                                <video src="${e.target.result}" controls class="img-fluid"></video>
                            </div>
                        `;
                    }
                    fileName.textContent = file.name;
                    fileActions.style.display = 'block';
                };
                
                reader.readAsDataURL(file);
            }

            function updateProcessButton() {
                const button = document.getElementById('processEvaluation');
                button.disabled = !selectedFile;
            }

            // Process evaluation
            document.getElementById('processEvaluation').addEventListener('click', async () => {
                if (!selectedFile) {
                    alert('Please select a file');
                    return;
                }

                const button = document.getElementById('processEvaluation');
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

                try {
                    const formData = new FormData();
                    formData.append('file', selectedFile);
                    formData.append('rubric_id', 'digital_art_evaluation'); // Default rubric

                    const response = await fetch('/api/evaluate/single', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error('Evaluation failed');
                    }

                    const result = await response.json();
                    evaluationResult = result;
                    displayResult(result);

                } catch (error) {
                    alert('Error processing evaluation: ' + error.message);
                } finally {
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-magic"></i> Evaluate with AI';
                }
            });

            function displayResult(result) {
                const container = document.getElementById('modalResultsContainer');
                const modal = document.getElementById('resultsModal');
                const viewResultsBtn = document.getElementById('viewResults');
                
                container.innerHTML = '';
                
                const card = createSubmissionCard(result, 0);
                container.appendChild(card);
                
                // Show "View Results" button
                viewResultsBtn.style.display = 'inline-block';
                
                // Show modal
                modal.style.display = 'flex';
            }
            
            function closeModal() {
                const modal = document.getElementById('resultsModal');
                modal.style.display = 'none';
            }
            
            function openModal() {
                const modal = document.getElementById('resultsModal');
                modal.style.display = 'flex';
            }
            
            // Close modal when clicking outside
            document.getElementById('resultsModal').addEventListener('click', function(e) {
                if (e.target === this) {
                    closeModal();
                }
            });

            function createSubmissionCard(result, index) {
                const card = document.createElement('div');
                card.className = 'results-card';
                
                card.innerHTML = `
                    <div class="score-display">
                        <div class="score-number">${result.overall_average_score.toFixed(1)}</div>
                        <div class="score-label">Overall Score</div>
                        <div class="mt-3">
                            <span class="status-badge ${result.overall_passed ? 'status-passed' : 'status-failed'}">
                                ${result.overall_passed ? 'PASSED' : 'FAILED'}
                            </span>
                            <span class="status-badge ${getEvaluationMode(result) === 'GEMINI AI' ? 'status-ai' : 'status-deterministic'} ms-2">
                                ${getEvaluationMode(result)}
                            </span>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <h5 class="card-title">${result.submission_title || `Submission ${index + 1}`}</h5>
                        <p class="card-text text-muted">${result.submission_description || 'No description provided'}</p>
                        
                        <div class="score-interpretation">
                            <h6><i class="fas fa-info-circle"></i> Score Interpretation:</h6>
                            <div>
                                <span class="score-range range-excellent">8.0-10.0</span><span class="score-range-label">Excellent</span>
                                <span class="score-range range-good">6.0-7.9</span><span class="score-range-label">Good</span>
                                <span class="score-range range-fair">4.0-5.9</span><span class="score-range-label">Fair</span>
                                <span class="score-range range-poor">0.0-3.9</span><span class="score-range-label">Needs Improvement</span>
                            </div>
                        </div>
                        
                        <h6>Criterion Breakdown:</h6>
                        ${result.rubric_results.map(rubricResult => `
                            <div class="mb-3">
                                <strong>${rubricResult.rubric_id}:</strong>
                                <span class="badge bg-primary ms-2">${rubricResult.overall_score.toFixed(1)}/10</span>
                                <div class="mt-2">
                                    ${rubricResult.criterion_scores.map(score => `
                                        <div class="criterion-item">
                                            <div class="criterion-name">${score.criterion_name}</div>
                                            <div class="criterion-score">${score.score.toFixed(1)}/10</div>
                                            <div class="criterion-feedback">${score.feedback}</div>
                                            <div class="criterion-reasoning">${score.reasoning}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                return card;
            }

            function getScoreClass(score) {
                if (score >= 8) return 'score-excellent';
                if (score >= 6) return 'score-good';
                if (score >= 4) return 'score-fair';
                return 'score-poor';
            }

            function getEvaluationMode(result) {
                // Check if any rubric result has fallback reason
                const hasFallback = result.rubric_results.some(rr => rr.fallback_reason);
                return hasFallback ? 'DETERMINISTIC' : 'GEMINI AI';
            }

            function getEvaluationModeBadge(result) {
                const mode = getEvaluationMode(result);
                return mode === 'GEMINI AI' ? 'bg-success' : 'bg-warning';
            }

            function exportResults() {
                if (evaluationResults.length === 0) {
                    alert('No results to export');
                    return;
                }
                
                const dataStr = JSON.stringify(evaluationResults, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'evaluation_results.json';
                link.click();
                URL.revokeObjectURL(url);
            }

            function clearResults() {
                evaluationResults = [];
                document.getElementById('resultsSection').style.display = 'none';
                document.getElementById('resultsContainer').innerHTML = '';
            }

            // Initialize page
            loadRubrics();
        </script>
    </body>
    </html>
    """

@app.get("/api/rubrics")
async def get_rubrics():
    """Get all available rubrics."""
    try:
        rubrics = rubric_manager.list_rubrics()
        return rubrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate/single")
async def evaluate_single(
    file: UploadFile = File(...),
    rubric_id: str = Form(...)
):
    """Process single file evaluation with parallel criteria processing."""
    try:
        # Load rubric
        rubric = rubric_manager.get_rubric(rubric_id)
        if not rubric:
            raise HTTPException(status_code=400, detail="Rubric not found")
        
        # Read file content
        content = await file.read()
        content_b64 = base64.b64encode(content).decode('utf-8')
        
        # Determine media type
        media_type = "image" if file.content_type.startswith("image/") else "video"
        
        # Create submission
        submission = MultimodalSubmission(
            id=str(uuid.uuid4()),
            rubric_ids=[rubric_id],
            media_items=[{
                "media_type": media_type,
                "content": content_b64,
                "metadata": {"filename": file.filename},
                "filename": file.filename
            }],
            title=f"Submission: {file.filename}",
            description=f"Uploaded file: {file.filename}"
        )
        
        # Evaluate with parallel criteria processing
        result = await evaluator.evaluate_submission_multi_rubric(
            submission, [rubric], ModelProvider.GOOGLE_GEMINI
        )
        
        # Add detailed feedback
        for rubric_result in result.rubric_results:
            if rubric_result.fallback_reason:
                rubric_result.criterion_scores = [
                    CriterionScore(
                        criterion_name=score.criterion_name,
                        score=score.score,
                        feedback=f"⚠️ FALLBACK MODE: {score.feedback}",
                        reasoning=f"This score was generated using deterministic evaluation because: {rubric_result.fallback_reason}. For real AI evaluation, please configure your Gemini API key."
                    ) for score in rubric_result.criterion_scores
                ]
            else:
                rubric_result.criterion_scores = [
                    CriterionScore(
                        criterion_name=score.criterion_name,
                        score=score.score,
                        feedback=f"🤖 AI EVALUATION: {score.feedback}",
                        reasoning=score.reasoning
                    ) for score in rubric_result.criterion_scores
                ]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate/batch")
async def evaluate_batch(
    files: List[UploadFile] = File(...),
    rubric_ids: List[str] = Form(...)
):
    """Process batch evaluation with multiple rubrics."""
    try:
        # Load rubrics
        rubrics = []
        for rubric_id in rubric_ids:
            rubric = rubric_manager.get_rubric(rubric_id)
            if rubric:
                rubrics.append(rubric)
        
        if not rubrics:
            raise HTTPException(status_code=400, detail="No valid rubrics found")
        
        # Process submissions
        submission_results = []
        batch_id = str(uuid.uuid4())
        
        for i, file in enumerate(files):
            try:
                # Read file content
                content = await file.read()
                content_b64 = base64.b64encode(content).decode('utf-8')
                
                # Determine media type
                media_type = "image" if file.content_type.startswith("image/") else "video"
                
                # Create submission
                submission = MultimodalSubmission(
                    id=str(uuid.uuid4()),
                    rubric_ids=rubric_ids,
                    media_items=[{
                        "media_type": media_type,
                        "content": content_b64,
                        "metadata": {"filename": file.filename},
                        "filename": file.filename
                    }],
                    batch_id=batch_id,
                    title=f"Submission {i+1}",
                    description=f"Uploaded file: {file.filename}"
                )
                
                # Evaluate with multiple rubrics
                result = await evaluator.evaluate_submission_multi_rubric(
                    submission, rubrics, ModelProvider.GOOGLE_GEMINI
                )
                
                # Add detailed feedback for each rubric result
                for rubric_result in result.rubric_results:
                    if rubric_result.fallback_reason:
                        # Add fallback explanation
                        rubric_result.criterion_scores = [
                            CriterionScore(
                                criterion_name=score.criterion_name,
                                score=score.score,
                                feedback=f"⚠️ FALLBACK MODE: {score.feedback}",
                                reasoning=f"This score was generated using deterministic evaluation because: {rubric_result.fallback_reason}. For real AI evaluation, please configure your Gemini API key."
                            ) for score in rubric_result.criterion_scores
                        ]
                    else:
                        # Add AI evaluation explanation
                        rubric_result.criterion_scores = [
                            CriterionScore(
                                criterion_name=score.criterion_name,
                                score=score.score,
                                feedback=f"🤖 AI EVALUATION: {score.feedback}",
                                reasoning=f"Score generated by Gemini Pro Vision AI model. This represents genuine AI analysis of your submission."
                            ) for score in rubric_result.criterion_scores
                        ]
                
                submission_results.append(result)
                
            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                continue
        
        return BatchEvaluationResult(
            batch_id=batch_id,
            submission_results=submission_results,
            batch_metadata={"total_files": len(files), "rubrics_used": rubric_ids},
            total_submissions=len(files),
            successful_evaluations=len(submission_results),
            failed_evaluations=len(files) - len(submission_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/submissions/{submission_id}/preview")
async def get_submission_preview(submission_id: str):
    """Get preview image for a submission."""
    # This would return the actual image data
    # For now, return a placeholder
    return {"message": "Preview endpoint - would return image data"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
