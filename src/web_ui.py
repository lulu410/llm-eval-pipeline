"""
Web UI for the LLM evaluation pipeline.
Provides user-friendly interface for rubric management, multimodal submissions,
and evaluation results viewing.
"""

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import json

from .api import app as api_app
from .rubric_manager import RubricManager

# Create UI sub-app
app = FastAPI(title="LLM Evaluation Pipeline UI")

# Mount the API app
app.mount("/api", api_app)

# Set up templates and static files
from pathlib import Path
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

# Static files directory (create if it doesn't exist)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Initialize rubric manager
rubric_manager = RubricManager()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    rubrics = rubric_manager.list_rubrics()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "rubrics": rubrics,
        "total_rubrics": len(rubrics)
    })


@app.get("/rubrics", response_class=HTMLResponse)
async def rubrics_page(request: Request):
    """Rubrics management page."""
    rubrics = rubric_manager.list_rubrics()
    return templates.TemplateResponse("rubrics.html", {
        "request": request,
        "rubrics": rubrics
    })


@app.get("/rubrics/create", response_class=HTMLResponse)
async def create_rubric_page(request: Request):
    """Create new rubric page."""
    return templates.TemplateResponse("create_rubric.html", {"request": request})


@app.post("/rubrics/create")
async def create_rubric_submit(
    request: Request,
    rubric_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    criteria_data: str = Form(...)
):
    """Handle rubric creation form submission."""
    try:
        criteria = json.loads(criteria_data)
        
        # Create rubric using the rubric manager directly
        rubric = rubric_manager.create_rubric(rubric_id, name, description, criteria)
        
        return RedirectResponse(url="/rubrics", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("create_rubric.html", {
            "request": request,
            "error": str(e)
        })


@app.get("/evaluate", response_class=HTMLResponse)
async def evaluate_page(request: Request):
    """Evaluation submission page."""
    rubrics = rubric_manager.list_rubrics()
    return templates.TemplateResponse("evaluate.html", {
        "request": request,
        "rubrics": rubrics
    })


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports viewing page."""
    return templates.TemplateResponse("reports.html", {"request": request})


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request})


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return templates.TemplateResponse("500.html", {"request": request})
