import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api_models import AnalysisRequest, FrontendAnalysisResponse
from db.database import init_db, get_db
from routers import options_router
from services import analysis_service


# --- App Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Initializing database...")
    init_db()
    logging.info("Database initialized.")
    logging.info("Loading NLP model...")
    # This ensures the spaCy model in analysis_service is loaded on startup.
    logging.info("NLP model loaded successfully.")
    yield
    logging.info("Shutting down.")


# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Wingman AI Backend - Guru Edition",
    description="Handles advanced conversation analysis for a stateless UI.",
    version="9.0.0",
    lifespan=lifespan
)

# --- Middlewares ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request {request.method} {request.url.path} processed in {process_time:.4f}s")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(options_router.router)


# --- Custom Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request body.", "errors": exc.errors()},
    )


# --- API Endpoints ---
@app.post("/api/v1/analyze", response_model=FrontendAnalysisResponse)
async def analyze_conversation(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Performs a full analysis of a conversation, saves the state to the database,
    and returns a response tailored for the frontend.
    """
    logger.info(f"Received analysis request for match: {request.matchId}")
    try:
        # Perform the full analysis
        analysis = analysis_service.run_full_conversation_analysis(
            db=db,
            match_id=request.matchId,
            scraped_data=request.scraped_data,
            ui_settings=request.ui_settings
        )

        # Map the full internal analysis object to the frontend-specific response model
        return FrontendAnalysisResponse(
            conversationState=analysis.conversationState,
            suppressGreeting=analysis.suppressGreeting,
            lastMessageAnalysis=analysis.lastMessageAnalysis,
            memory=analysis.memory,
            dateAnalysis=analysis.dateAnalysis,
            sexualAnalysis=analysis.sexualAnalysis,
            responseSuggestions=analysis.responseSuggestions,
            geoContext=analysis.geoContext
        )
    except Exception as e:
        logger.error(f"An error occurred during analysis for {request.matchId}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/health", tags=["System"])
def health_check():
    """Provides a simple health check for the service."""
    return {"status": "ok", "version": app.version}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
