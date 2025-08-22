from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
from typing import Dict, Any
import asyncio
import json
import uuid

from src.asdsadf_agent import ASDSADFAgent
from src.models import UserQuery, QueryResponse, SystemHealth
from src.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ASDSADF - AI RAG Learning Assistant",
    description="Aspiring Developer's Skill Acquisition and Development Framework",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: ASDSADFAgent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on application startup."""
    global agent
    try:
        logger.info("Initializing ASDSADF Agent...")
        agent = ASDSADFAgent()
        # Expose agent on app.state so request handlers can reliably access it
        app.state.agent = agent

        # Initialize agent in background to avoid blocking startup
        initialization_success = await agent.initialize()

        if initialization_success:
            logger.info("ASDSADF Agent initialized successfully")
            # Ensure the app.state reference is the initialized instance
            app.state.agent = agent
        else:
            logger.error("Failed to initialize ASDSADF Agent")
            # Mark absent so endpoints can respond appropriately
            app.state.agent = None

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Ensure state is consistent on error
        app.state.agent = None

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    logger.info("Shutting down ASDSADF application")
    try:
        a = getattr(app.state, "agent", None)
        if a:
            # attempt graceful cleanup if agent exposes one
            if hasattr(a, "shutdown"):
                try:
                    maybe_coro = a.shutdown()
                    if asyncio.iscoroutine(maybe_coro):
                        await maybe_coro
                except Exception as e:
                    logger.debug("Agent.shutdown() raised: %s", e)
        # Remove agent from state
        app.state.agent = None
    except Exception as e:
        logger.debug("Error during shutdown cleanup: %s", e)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    try:
        with open("src/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>ASDSADF - AI Learning Assistant</title></head>
        <body>
            <h1>🚀 ASDSADF</h1>
            <p>Aspiring Developer's Skill Acquisition and Development Framework</p>
            <p>API is running! Visit <a href="/docs">/docs</a> for API documentation.</p>
        </body>
        </html>
        """)

@app.post("/chat")
async def chat_endpoint(request: Request, payload: UserQuery):
    """
    Robust /chat endpoint wrapper.
    Returns:
      - 200 + {"success": True, "data": ..., "context": [...]} on success
      - 503 + {"success": False, "error": "..."} if agent not initialized
      - 200 + {"success": False, "error": "..."} on processing exceptions (keeps frontend from showing 'undefined')
    """
    agent = getattr(request.app.state, "agent", None)
    if agent is None:
        logger.error("Agent not found in app.state")
        return JSONResponse(status_code=503, content={"success": False, "error": "Agent not available. Server not initialized."})

    if not getattr(agent, "initialized", False):
        logger.warning("Request received but agent not initialized")
        return JSONResponse(status_code=503, content={"success": False, "error": "Agent not initialized. Try again shortly."})

    try:
        result = await agent.process_query(payload)
        # result may be a QueryResponse dataclass-like object
        # Normalize to plain dicts so frontend parsing is easy
        resp_content = None
        context_used = []
        retrieval_sources = []
        processing_time = None

        if hasattr(result, "response"):
            resp_content = result.response
        else:
            resp_content = result

        if hasattr(result, "context_used"):
            context_used = result.context_used or []
        if hasattr(result, "retrieval_sources"):
            retrieval_sources = result.retrieval_sources or []
        if hasattr(result, "processing_time"):
            processing_time = result.processing_time

        # Ensure JSON-serializable values (fast-path; if non-serializable, fallback to string)
        try:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": resp_content,
                    "context": context_used,
                    "sources": retrieval_sources,
                    "processing_time": processing_time,
                },
            )
        except TypeError:
            # Fallback: stringify the data to avoid frontend undefined errors
            logger.exception("Non-serializable response payload, stringifying.")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": str(resp_content),
                    "context": context_used,
                    "sources": retrieval_sources,
                    "processing_time": processing_time,
                },
            )

    except Exception as e:
        logger.exception("Unhandled error in /chat: %s", e)
        # Return 200 with success False to ensure frontend receives a predictable JSON body
        return JSONResponse(status_code=200, content={"success": False, "error": str(e)})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not agent:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Agent not initialized"}
        )
    
    health_status = await agent.get_health_status()
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health_status)

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a specific session."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    session_info = agent.get_session_info(session_id)
    return JSONResponse(content=session_info)

@app.post("/knowledge/upload")
async def upload_knowledge(background_tasks: BackgroundTasks):
    """Upload knowledge documents to the RAG system."""
    if not agent or not agent.rag_system:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    # This would typically handle file uploads
    # For now, return a placeholder response
    return JSONResponse(content={
        "message": "Knowledge upload endpoint - implementation depends on your data sources",
        "status": "ready"
    })

@app.get("/knowledge/stats")
async def get_knowledge_stats():
    """Get statistics about the knowledge base."""
    if not agent or not agent.rag_system:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    stats = await agent.rag_system.get_collection_stats()
    return JSONResponse(content=stats)

@app.post("/evaluate")
async def run_evaluation():
    """Run the evaluation pipeline."""
    try:
        from evaluation.run_evaluation import run_evaluation_pipeline
        await run_evaluation_pipeline(agent)
        return JSONResponse(content={"status": "evaluation completed"})
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.post("/knowledge/add")
async def add_knowledge(data: dict, background_tasks: BackgroundTasks):
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    # expects { "title": "...", "content": "...", "source": "...", "document_type": "..." }
    doc = data
    background_tasks.add_task(_background_add, doc)
    return {"message": "Adding document in background"}


async def _background_add(doc: dict):
    from src.models import KnowledgeDocument
    kd = KnowledgeDocument(id=doc.get("id") or str(uuid.uuid4()), title=doc["title"], content=doc["content"], source=doc.get("source","unknown"), document_type=doc.get("document_type","documentation"), metadata=doc.get("metadata",{}))
    await agent.rag.add_document(kd)