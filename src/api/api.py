#!/usr/bin/env python3
"""
FastAPI-based REST API for AllSeeingEye
"""

import os
import json
import tempfile
import logging
import shutil
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from enum import Enum

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, BackgroundTasks, Form, Query, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Create logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AllSeeingEye-API")

# Import AllSeeingEye components
try:
    from ..core.analyzer import EfficientAnalyzer
    from ..llm.integration import get_llm_integration
    from ..utils.cache import Cache
    
    # Import visualization modules
    from ..visualization.dependency_graph import DependencyGraph
    from ..visualization.codebase_structure import CodebaseTreemap
    from ..visualization.metrics_dashboard import MetricsDashboard
    VISUALIZATION_AVAILABLE = True
    
    # Import similarity modules
    from ..similarity.code_similarity import CodeSimilarityAnalyzer
    from ..similarity.refactoring_suggestions import RefactoringSuggestionGenerator
    SIMILARITY_AVAILABLE = True
    
except ImportError:
    # Alternative import path
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from src.core.analyzer import EfficientAnalyzer
    from src.llm.integration import get_llm_integration
    from src.utils.cache import Cache
    
    # Import visualization modules
    try:
        from src.visualization.dependency_graph import DependencyGraph
        from src.visualization.codebase_structure import CodebaseTreemap
        from src.visualization.metrics_dashboard import MetricsDashboard
        VISUALIZATION_AVAILABLE = True
    except ImportError:
        VISUALIZATION_AVAILABLE = False
        logger.warning("Visualization modules not available")
    
    # Import similarity modules
    try:
        from src.similarity.code_similarity import CodeSimilarityAnalyzer
        from src.similarity.refactoring_suggestions import RefactoringSuggestionGenerator
        SIMILARITY_AVAILABLE = True
    except ImportError:
        SIMILARITY_AVAILABLE = False
        logger.warning("Similarity modules not available")

# Define API models
class AnalysisRequest(BaseModel):
    """Model for analysis request parameters"""
    directory: Optional[str] = None
    exclude_dirs: List[str] = Field(default_factory=lambda: [".git", "node_modules", "__pycache__"])
    output_format: str = "json"
    use_llm: bool = False
    llm_provider: Optional[str] = "ollama"
    llm_model: Optional[str] = "gemma:7b"
    max_workers: int = 4
    chunk_size: int = 100
    
class AnalysisResponse(BaseModel):
    """Model for analysis response"""
    task_id: str
    status: str
    message: str

class AnalysisResult(BaseModel):
    """Model for analysis result"""
    task_id: str
    status: str
    result: Dict[str, Any]
    output_file: Optional[str] = None

class LLMRequest(BaseModel):
    """Model for LLM request"""
    provider: str
    model: Optional[str] = None
    prompt: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class LLMResponse(BaseModel):
    """Model for LLM response"""
    text: str
    
class VisualizationMetric(str, Enum):
    """Enumeration of metrics used for visualizations"""
    SIZE = "size"
    LINES = "lines"

class VisualizationRequest(BaseModel):
    """Model for visualization request parameters"""
    directory: Optional[str] = None
    exclude_dirs: List[str] = Field(default_factory=lambda: [".git", "node_modules", "__pycache__"])
    exclude_files: List[str] = Field(default_factory=list)
    metric: VisualizationMetric = VisualizationMetric.SIZE

class SimilarityRequest(BaseModel):
    """Model for code similarity request parameters"""
    directory: Optional[str] = None
    exclude_dirs: List[str] = Field(default_factory=lambda: [".git", "node_modules", "__pycache__"])
    exclude_files: List[str] = Field(default_factory=list)
    min_clone_size: int = 20
    min_fragment_count: int = 2
    suggest_refactoring: bool = True

class WebhookConfig(BaseModel):
    """Model for webhook configuration"""
    url: str
    events: List[str] = ["analysis_complete", "analysis_failed"]
    headers: Optional[Dict[str, str]] = None

class TaskStatus(BaseModel):
    """Model for task status"""
    task_id: str
    status: str
    progress: float
    message: str
    
# Task management
tasks = {}

def create_app():
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="AllSeeingEye API",
        description="REST API for the AllSeeingEye codebase analysis tool",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create temporary directory for uploads
    os.makedirs(os.path.join(tempfile.gettempdir(), "allseeingeye_uploads"), exist_ok=True)
    
    # Initialize cache
    cache = Cache(cache_dir=os.path.join(tempfile.gettempdir(), "allseeingeye_api_cache"))
    
    # Define API routes
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "AllSeeingEye API",
            "version": "1.0.0",
            "documentation": "/docs"
        }
    
    @app.post("/analyze", response_model=AnalysisResponse)
    async def analyze_directory(
        request: AnalysisRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Analyze a directory with AllSeeingEye
        """
        # Validate directory
        if not request.directory:
            raise HTTPException(status_code=400, detail="Directory is required")
        
        if not os.path.exists(request.directory):
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Analysis queued",
            "result": None,
            "output_file": None
        }
        
        # Add task to background processing
        background_tasks.add_task(
            _process_analysis,
            task_id,
            request.directory,
            request.exclude_dirs,
            request.output_format,
            request.use_llm,
            request.llm_provider,
            request.llm_model,
            request.max_workers,
            request.chunk_size
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Analysis task queued"
        }
    
    @app.post("/analyze/upload", response_model=AnalysisResponse)
    async def analyze_upload(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        exclude_dirs: str = Form(".git,node_modules,__pycache__"),
        output_format: str = Form("json"),
        use_llm: bool = Form(False),
        llm_provider: Optional[str] = Form(None),
        llm_model: Optional[str] = Form(None),
        max_workers: int = Form(4),
        chunk_size: int = Form(100)
    ):
        """
        Analyze an uploaded ZIP file with AllSeeingEye
        """
        # Process ZIP file
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")
        
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_dir = os.path.join(tempfile.gettempdir(), "allseeingeye_uploads", task_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        zip_path = os.path.join(upload_dir, file.filename)
        with open(zip_path, "wb") as f:
            f.write(await file.read())
        
        # Extract ZIP file
        import zipfile
        extract_dir = os.path.join(upload_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            shutil.rmtree(upload_dir)
            raise HTTPException(status_code=400, detail=f"Failed to extract ZIP file: {str(e)}")
        
        # Parse exclude_dirs
        exclude_dirs_list = [d.strip() for d in exclude_dirs.split(",") if d.strip()]
        
        # Initialize task status
        tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Zip extracted, analysis queued",
            "result": None,
            "output_file": None,
            "upload_dir": upload_dir  # Store upload dir for cleanup
        }
        
        # Add task to background processing
        background_tasks.add_task(
            _process_analysis,
            task_id,
            extract_dir,
            exclude_dirs_list,
            output_format,
            use_llm,
            llm_provider,
            llm_model,
            max_workers,
            chunk_size
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Upload processed, analysis task queued"
        }
    
    @app.get("/analyze/{task_id}/status", response_model=TaskStatus)
    async def get_task_status(task_id: str):
        """
        Get the status of an analysis task
        """
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task_id,
            "status": tasks[task_id]["status"],
            "progress": tasks[task_id]["progress"],
            "message": tasks[task_id]["message"]
        }
    
    @app.get("/analyze/{task_id}/result", response_model=AnalysisResult)
    async def get_task_result(task_id: str):
        """
        Get the result of an analysis task
        """
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if tasks[task_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Task is not completed. Current status: {tasks[task_id]['status']}")
        
        return {
            "task_id": task_id,
            "status": tasks[task_id]["status"],
            "result": tasks[task_id]["result"],
            "output_file": tasks[task_id]["output_file"]
        }
    
    @app.get("/analyze/{task_id}/download")
    async def download_result(task_id: str):
        """
        Download the output file of an analysis task
        """
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if tasks[task_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Task is not completed. Current status: {tasks[task_id]['status']}")
        
        if not tasks[task_id]["output_file"] or not os.path.exists(tasks[task_id]["output_file"]):
            raise HTTPException(status_code=404, detail="Output file not found")
        
        return FileResponse(
            tasks[task_id]["output_file"],
            media_type="application/octet-stream",
            filename=os.path.basename(tasks[task_id]["output_file"])
        )
    
    @app.delete("/analyze/{task_id}")
    async def delete_task(task_id: str):
        """
        Delete an analysis task and its resources
        """
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Clean up upload directory if it exists
        if "upload_dir" in tasks[task_id] and os.path.exists(tasks[task_id]["upload_dir"]):
            try:
                shutil.rmtree(tasks[task_id]["upload_dir"])
            except Exception as e:
                logger.error(f"Failed to clean up upload directory: {e}")
        
        # Remove task from task store
        task_data = tasks.pop(task_id)
        
        return {
            "task_id": task_id,
            "status": "deleted",
            "message": "Task and associated resources deleted"
        }
    
    @app.post("/llm/generate", response_model=LLMResponse)
    async def generate_llm_response(request: LLMRequest):
        """
        Generate a response from an LLM
        """
        try:
            # Initialize LLM integration
            llm = get_llm_integration(
                provider=request.provider,
                config={
                    "model": request.model,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            )
            
            # Check if LLM is available
            if not llm.is_available():
                raise HTTPException(status_code=400, detail=f"LLM provider '{request.provider}' is not available")
            
            # Generate response
            response = llm.provider.generate(
                request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            # Extract text from response
            text = response.get("text", "")
            if not text and "error" in response:
                raise HTTPException(status_code=500, detail=f"LLM error: {response['error']}")
            
            return {"text": text}
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/webhooks/register")
    async def register_webhook(config: WebhookConfig, request: Request):
        """
        Register a webhook for event notifications
        """
        # Validate URL format
        import validators
        if not validators.url(config.url):
            raise HTTPException(status_code=400, detail="Invalid webhook URL")
        
        # Get client IP for logging/tracking
        client_ip = request.client.host
        
        # Generate webhook ID
        import uuid
        webhook_id = str(uuid.uuid4())
        
        # Store webhook config
        # Note: In a production app, this would be stored in a database
        if not hasattr(app, "webhooks"):
            app.webhooks = {}
        
        import datetime
        app.webhooks[webhook_id] = {
            "id": webhook_id,
            "url": config.url,
            "events": config.events,
            "headers": config.headers or {},
            "created_by": client_ip,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        return {
            "webhook_id": webhook_id,
            "status": "registered",
            "message": "Webhook registered successfully"
        }
    
    @app.delete("/webhooks/{webhook_id}")
    async def delete_webhook(webhook_id: str):
        """
        Delete a registered webhook
        """
        if not hasattr(app, "webhooks") or webhook_id not in app.webhooks:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Remove webhook
        webhook = app.webhooks.pop(webhook_id)
        
        return {
            "webhook_id": webhook_id,
            "status": "deleted",
            "message": "Webhook deleted successfully"
        }
        
    # Visualization endpoints
    
    @app.post("/visualize/dependency-graph", response_model=AnalysisResponse)
    async def generate_dependency_graph(
        request: VisualizationRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Generate a dependency graph visualization for a directory
        """
        if not VISUALIZATION_AVAILABLE:
            raise HTTPException(status_code=501, detail="Visualization modules not available")
            
        # Validate directory
        if not request.directory:
            raise HTTPException(status_code=400, detail="Directory is required")
        
        if not os.path.exists(request.directory):
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Dependency graph generation queued",
            "result": None,
            "output_file": None,
            "visualization_type": "dependency-graph"
        }
        
        # Add task to background processing
        background_tasks.add_task(
            _process_dependency_graph,
            task_id,
            request.directory,
            request.exclude_dirs,
            request.exclude_files
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Dependency graph task queued"
        }
    
    @app.post("/visualize/treemap", response_model=AnalysisResponse)
    async def generate_treemap(
        request: VisualizationRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Generate a codebase structure treemap visualization for a directory
        """
        if not VISUALIZATION_AVAILABLE:
            raise HTTPException(status_code=501, detail="Visualization modules not available")
            
        # Validate directory
        if not request.directory:
            raise HTTPException(status_code=400, detail="Directory is required")
        
        if not os.path.exists(request.directory):
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Treemap generation queued",
            "result": None,
            "output_file": None,
            "visualization_type": "treemap"
        }
        
        # Add task to background processing
        background_tasks.add_task(
            _process_treemap,
            task_id,
            request.directory,
            request.exclude_dirs,
            request.exclude_files,
            request.metric
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Treemap task queued"
        }
    
    @app.post("/visualize/metrics-dashboard", response_model=AnalysisResponse)
    async def generate_metrics_dashboard(
        request: VisualizationRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Generate a metrics dashboard visualization for a directory
        """
        if not VISUALIZATION_AVAILABLE:
            raise HTTPException(status_code=501, detail="Visualization modules not available")
            
        # Validate directory
        if not request.directory:
            raise HTTPException(status_code=400, detail="Directory is required")
        
        if not os.path.exists(request.directory):
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Metrics dashboard generation queued",
            "result": None,
            "output_file": None,
            "visualization_type": "metrics-dashboard"
        }
        
        # Add task to background processing
        background_tasks.add_task(
            _process_metrics_dashboard,
            task_id,
            request.directory,
            request.exclude_dirs,
            request.exclude_files
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Metrics dashboard task queued"
        }
    
    @app.get("/visualize/{task_id}/view")
    async def view_visualization(task_id: str):
        """
        View a generated visualization directly
        """
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if tasks[task_id]["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Task is not completed. Current status: {tasks[task_id]['status']}")
        
        if not tasks[task_id]["output_file"] or not os.path.exists(tasks[task_id]["output_file"]):
            raise HTTPException(status_code=404, detail="Output file not found")
        
        # Read the HTML file
        with open(tasks[task_id]["output_file"], "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Return as HTML response
        return HTMLResponse(content=html_content)
    
    # Similarity analysis endpoints
    
    @app.post("/similarity/analyze", response_model=AnalysisResponse)
    async def analyze_code_similarity(
        request: SimilarityRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Analyze code similarity in a directory
        """
        if not SIMILARITY_AVAILABLE:
            raise HTTPException(status_code=501, detail="Similarity modules not available")
            
        # Validate directory
        if not request.directory:
            raise HTTPException(status_code=400, detail="Directory is required")
        
        if not os.path.exists(request.directory):
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        # Generate task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Code similarity analysis queued",
            "result": None,
            "output_file": None,
            "similarity_type": "code-similarity"
        }
        
        # Add task to background processing
        background_tasks.add_task(
            _process_code_similarity,
            task_id,
            request.directory,
            request.exclude_dirs,
            request.exclude_files,
            request.min_clone_size,
            request.suggest_refactoring,
            request.min_fragment_count
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Code similarity analysis task queued"
        }
    
    # Helper function for background processing
    async def _process_analysis(
        task_id,
        directory,
        exclude_dirs,
        output_format,
        use_llm,
        llm_provider,
        llm_model,
        max_workers,
        chunk_size
    ):
        """Process analysis task in background"""
        try:
            # Update task status
            tasks[task_id]["status"] = "processing"
            tasks[task_id]["message"] = "Analysis in progress"
            
            # Initialize analyzer with progress callback
            def progress_callback(progress, message):
                tasks[task_id]["progress"] = progress
                tasks[task_id]["message"] = message
            
            # Initialize analyzer
            analyzer = EfficientAnalyzer(
                directory=directory,
                excluded_dirs=exclude_dirs,
                output_format=output_format,
                max_workers=max_workers,
                chunk_size=chunk_size,
                progress_callback=progress_callback
            )
            
            # Initialize LLM if requested
            if use_llm and llm_provider:
                llm = get_llm_integration(
                    provider=llm_provider,
                    config={"model": llm_model} if llm_model else None
                )
                
                if llm.is_available():
                    analyzer.llm_integration = llm
            
            # Run analysis
            output_file = analyzer.run()
            
            # Load results
            with open(output_file, 'r') as f:
                if output_format == "json":
                    result = json.load(f)
                else:
                    result = {"content": f.read()}
            
            # Update task status
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["message"] = "Analysis completed"
            tasks[task_id]["result"] = result
            tasks[task_id]["output_file"] = output_file
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("analysis_complete", {
                    "task_id": task_id,
                    "status": "completed",
                    "directory": directory,
                    "output_format": output_format
                })
                
        except Exception as e:
            logger.error(f"Error processing analysis: {e}")
            
            # Update task status
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"Analysis failed: {str(e)}"
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("analysis_failed", {
                    "task_id": task_id,
                    "status": "failed",
                    "directory": directory,
                    "error": str(e)
                })
    
    async def _trigger_webhooks(event, data):
        """Trigger webhooks for an event"""
        import aiohttp
        import asyncio
        
        if not hasattr(app, "webhooks"):
            return
        
        for webhook_id, webhook in app.webhooks.items():
            if event in webhook["events"]:
                import datetime
                # Prepare payload
                payload = {
                    "event": event,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "data": data
                }
                
                # Send webhook request asynchronously
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            webhook["url"],
                            json=payload,
                            headers=webhook["headers"],
                            timeout=10
                        ) as response:
                            logger.info(f"Webhook {webhook_id} triggered: {response.status}")
                except Exception as e:
                    logger.error(f"Failed to trigger webhook {webhook_id}: {e}")
    
    # Regular cleanup task to remove old tasks
    @app.on_event("startup")
    async def startup_event():
        """Start background task for cleanup"""
        background_tasks = BackgroundTasks()
        background_tasks.add_task(_cleanup_old_tasks)
    
    # Helper functions for visualization tasks
    async def _process_dependency_graph(
        task_id,
        directory,
        exclude_dirs,
        exclude_files
    ):
        """Process dependency graph generation in background"""
        try:
            # Update task status
            tasks[task_id]["status"] = "processing"
            tasks[task_id]["message"] = "Building dependency graph"
            tasks[task_id]["progress"] = 0.3
            
            # Create cache directory
            cache_dir = os.path.join(tempfile.gettempdir(), "allseeingeye_api_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Initialize dependency graph
            dep_graph = DependencyGraph(
                base_directory=directory,
                excluded_dirs=exclude_dirs,
                max_file_size=1024 * 1024,  # 1MB
                cache_dir=cache_dir
            )
            
            # Build graph
            tasks[task_id]["message"] = "Building graph structure"
            tasks[task_id]["progress"] = 0.5
            dep_graph.build_graph()
            
            # Generate output path
            base_name = os.path.basename(directory)
            output_file = os.path.join(cache_dir, f"{base_name}_dependency_graph_{task_id}.html")
            
            # Generate visualization
            tasks[task_id]["message"] = "Generating visualization"
            tasks[task_id]["progress"] = 0.8
            dep_graph.generate_html(output_file)
            
            # Get graph stats
            stats = dep_graph.get_stats()
            
            # Update task status
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["message"] = "Dependency graph generated"
            tasks[task_id]["result"] = stats
            tasks[task_id]["output_file"] = output_file
            import time
            tasks[task_id]["completion_time"] = time.time()
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("visualization_complete", {
                    "task_id": task_id,
                    "status": "completed",
                    "visualization_type": "dependency-graph",
                    "directory": directory
                })
                
        except Exception as e:
            logger.error(f"Error generating dependency graph: {e}")
            
            # Update task status
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"Dependency graph generation failed: {str(e)}"
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("visualization_failed", {
                    "task_id": task_id,
                    "status": "failed",
                    "visualization_type": "dependency-graph",
                    "directory": directory,
                    "error": str(e)
                })
    
    async def _process_treemap(
        task_id,
        directory,
        exclude_dirs,
        exclude_files,
        metric
    ):
        """Process treemap generation in background"""
        try:
            # Update task status
            tasks[task_id]["status"] = "processing"
            tasks[task_id]["message"] = "Building directory structure"
            tasks[task_id]["progress"] = 0.3
            
            # Create cache directory
            cache_dir = os.path.join(tempfile.gettempdir(), "allseeingeye_api_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Initialize treemap
            treemap = CodebaseTreemap(
                base_directory=directory,
                excluded_dirs=exclude_dirs,
                excluded_files=exclude_files,
                max_file_size=1024 * 1024,  # 1MB
                metric=metric,
                cache_dir=cache_dir
            )
            
            # Build treemap data
            tasks[task_id]["message"] = "Analyzing codebase structure"
            tasks[task_id]["progress"] = 0.5
            treemap.build_treemap_data()
            
            # Generate output path
            base_name = os.path.basename(directory)
            output_file = os.path.join(cache_dir, f"{base_name}_treemap_{task_id}.html")
            
            # Generate visualization
            tasks[task_id]["message"] = "Generating visualization"
            tasks[task_id]["progress"] = 0.8
            treemap.generate_html(
                output_file,
                title=f"Codebase Structure: {base_name}"
            )
            
            # Get treemap stats
            stats = treemap.get_stats()
            
            # Update task status
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["message"] = "Treemap visualization generated"
            tasks[task_id]["result"] = stats
            tasks[task_id]["output_file"] = output_file
            import time
            tasks[task_id]["completion_time"] = time.time()
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("visualization_complete", {
                    "task_id": task_id,
                    "status": "completed",
                    "visualization_type": "treemap",
                    "directory": directory
                })
                
        except Exception as e:
            logger.error(f"Error generating treemap: {e}")
            
            # Update task status
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"Treemap generation failed: {str(e)}"
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("visualization_failed", {
                    "task_id": task_id,
                    "status": "failed",
                    "visualization_type": "treemap",
                    "directory": directory,
                    "error": str(e)
                })
    
    async def _process_metrics_dashboard(
        task_id,
        directory,
        exclude_dirs,
        exclude_files
    ):
        """Process metrics dashboard generation in background"""
        try:
            # Update task status
            tasks[task_id]["status"] = "processing"
            tasks[task_id]["message"] = "Analyzing codebase metrics"
            tasks[task_id]["progress"] = 0.3
            
            # Create cache directory
            cache_dir = os.path.join(tempfile.gettempdir(), "allseeingeye_api_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Initialize metrics dashboard
            dashboard = MetricsDashboard(
                base_directory=directory,
                excluded_dirs=exclude_dirs,
                excluded_files=exclude_files,
                max_file_size=1024 * 1024,  # 1MB
                cache_dir=cache_dir
            )
            
            # Calculate metrics
            tasks[task_id]["message"] = "Calculating codebase metrics"
            tasks[task_id]["progress"] = 0.5
            metrics_data = dashboard.calculate_metrics()
            
            # Generate output path
            base_name = os.path.basename(directory)
            output_file = os.path.join(cache_dir, f"{base_name}_metrics_{task_id}.html")
            
            # Generate visualization
            tasks[task_id]["message"] = "Generating dashboard"
            tasks[task_id]["progress"] = 0.8
            dashboard.generate_html(
                output_file,
                title=f"Codebase Metrics: {base_name}"
            )
            
            # Update task status
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["message"] = "Metrics dashboard generated"
            tasks[task_id]["result"] = metrics_data
            tasks[task_id]["output_file"] = output_file
            import time
            tasks[task_id]["completion_time"] = time.time()
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("visualization_complete", {
                    "task_id": task_id,
                    "status": "completed",
                    "visualization_type": "metrics-dashboard",
                    "directory": directory
                })
                
        except Exception as e:
            logger.error(f"Error generating metrics dashboard: {e}")
            
            # Update task status
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"Metrics dashboard generation failed: {str(e)}"
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("visualization_failed", {
                    "task_id": task_id,
                    "status": "failed",
                    "visualization_type": "metrics-dashboard",
                    "directory": directory,
                    "error": str(e)
                })

    # Helper functions for similarity analysis
    async def _process_code_similarity(
        task_id,
        directory,
        exclude_dirs,
        exclude_files,
        min_clone_size,
        suggest_refactoring,
        min_fragment_count
    ):
        """Process code similarity analysis in background"""
        try:
            # Update task status
            tasks[task_id]["status"] = "processing"
            tasks[task_id]["message"] = "Analyzing code files"
            tasks[task_id]["progress"] = 0.1
            
            # Create cache directory
            cache_dir = os.path.join(tempfile.gettempdir(), "allseeingeye_api_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Initialize similarity analyzer
            similarity_analyzer = CodeSimilarityAnalyzer(
                base_directory=directory,
                excluded_dirs=exclude_dirs,
                excluded_files=exclude_files,
                max_file_size=1024 * 1024,  # 1MB
                min_clone_size=min_clone_size,
                cache_dir=cache_dir
            )
            
            # Analyze code similarity
            tasks[task_id]["message"] = "Detecting code duplication"
            tasks[task_id]["progress"] = 0.4
            similarity_results = similarity_analyzer.analyze_codebase()
            
            # Generate output path for similarity results
            base_name = os.path.basename(directory)
            similarity_output = os.path.join(cache_dir, f"{base_name}_code_similarity_{task_id}.json")
            
            # Save similarity results
            with open(similarity_output, 'w') as f:
                json.dump(similarity_results, f, indent=2)
            
            # Generate refactoring suggestions if requested
            suggestions = None
            suggestions_output = None
            if suggest_refactoring:
                tasks[task_id]["message"] = "Generating refactoring suggestions"
                tasks[task_id]["progress"] = 0.7
                
                # Initialize suggestion generator
                suggestion_generator = RefactoringSuggestionGenerator(
                    base_directory=directory,
                    min_fragment_count=min_fragment_count,
                    min_token_count=min_clone_size
                )
                
                # Generate suggestions
                suggestions = suggestion_generator.generate_suggestions(
                    similarity_results=similarity_results,
                    analyzer=similarity_analyzer
                )
                
                # Generate output path for suggestions
                suggestions_output = os.path.join(cache_dir, f"{base_name}_refactoring_suggestions_{task_id}.json")
                
                # Save suggestions
                with open(suggestions_output, 'w') as f:
                    json.dump(suggestions, f, indent=2)
            
            # Update task status
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["message"] = "Code similarity analysis completed"
            tasks[task_id]["result"] = {
                "similarity": similarity_results,
                "suggestions": suggestions
            }
            tasks[task_id]["output_file"] = similarity_output
            tasks[task_id]["suggestions_file"] = suggestions_output if suggestions else None
            import time
            tasks[task_id]["completion_time"] = time.time()
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("similarity_analysis_complete", {
                    "task_id": task_id,
                    "status": "completed",
                    "directory": directory,
                    "has_suggestions": suggestions is not None
                })
                
        except Exception as e:
            logger.error(f"Error analyzing code similarity: {e}")
            
            # Update task status
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"Code similarity analysis failed: {str(e)}"
            
            # Trigger webhooks if configured
            if hasattr(app, "webhooks"):
                await _trigger_webhooks("similarity_analysis_failed", {
                    "task_id": task_id,
                    "status": "failed",
                    "directory": directory,
                    "error": str(e)
                })

    async def _cleanup_old_tasks():
        """Clean up old tasks and temporary files"""
        import asyncio
        import time
        
        while True:
            # Sleep for 1 hour
            await asyncio.sleep(3600)
            
            # Get current time
            current_time = time.time()
            
            # Find tasks older than 24 hours
            tasks_to_remove = []
            for task_id, task in tasks.items():
                # Check if task has a completion time
                if "completion_time" in task and current_time - task["completion_time"] > 86400:
                    tasks_to_remove.append(task_id)
            
            # Remove old tasks
            for task_id in tasks_to_remove:
                if "upload_dir" in tasks[task_id] and os.path.exists(tasks[task_id]["upload_dir"]):
                    try:
                        shutil.rmtree(tasks[task_id]["upload_dir"])
                    except Exception as e:
                        logger.error(f"Failed to clean up upload directory: {e}")
                
                del tasks[task_id]
            
            if tasks_to_remove:
                logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
    
    return app

# Create app instance for direct import
app = create_app()

if __name__ == "__main__":
    # Run with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
