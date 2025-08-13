import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api_models import AnalysisRequest, RegenerationRequest, FullApiResponse, PromptGenerationResponse
from db.database import init_db, get_db
from routers import options_router
from services import analysis_service, prompt_service


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
    description="Handles advanced conversation analysis, persistent memory, and dynamic prompt engineering for a stateless UI.",
    version="8.0.0",
    lifespan=lifespan
)

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
@app.post("/api/v1/analyze", response_model=FullApiResponse)
async def analyze_conversation(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Performs a full analysis of a conversation, saves the state to the database,
    and returns the complete analysis object along with an initial set of prompts
    based on smart defaults. This is the primary endpoint for a new session.
    """
    logger.info(f"Received analysis request for match: {request.matchId}")
    with open('load.json', 'a+') as f:
        f.write(',\n' +request.model_dump_json(indent=4))

    try:
        # Perform the full analysis
        analysis = analysis_service.run_full_conversation_analysis(
            db=db,
            match_id=request.matchId,
            scraped_data=request.scraped_data,
            ui_settings=request.ui_settings
        )

        # Generate smart defaults for the first prompt generation
        applied_settings = analysis_service.get_initial_ui_settings(analysis, request.ui_settings)

        # Generate the initial prompts
        prompts = prompt_service.generate_prompts(
            analysis=analysis,
            scraped_data=request.scraped_data,
            ui_settings=applied_settings
        )
        with open('analysis.json', 'a+') as f:
            f.write(',\n' + FullApiResponse(
                prompts=prompts,
                full_analysis=analysis,
                applied_ui_settings=applied_settings
            ).model_dump_json(indent=4))
        return FullApiResponse(
            prompts=prompts,
            full_analysis=analysis,
            applied_ui_settings=applied_settings
        )
    except Exception as e:
        logger.error(f"An error occurred during analysis for {request.matchId}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.post("/api/v1/regenerate", response_model=PromptGenerationResponse)
async def regenerate_prompts(request: RegenerationRequest, db: Session = Depends(get_db)):
    """
    Regenerates prompts using a previously completed analysis (loaded from DB)
    but with new, user-provided UI settings and overrides. This is a lightweight
    operation that returns only the prompt object.
    """
    logger.info(f"Received regeneration request for match: {request.matchId}")
    try:
        # Load the latest analysis from the database
        latest_analysis = analysis_service.load_and_apply_overrides(
            db=db,
            match_id=request.matchId,
            ui_settings=request.ui_settings
        )

        # Generate new prompts with the overridden analysis and new settings
        prompts = prompt_service.generate_prompts(
            analysis=latest_analysis,
            scraped_data=request.scraped_data,  # Scraped data is needed for context
            ui_settings=request.ui_settings
        )

        return prompts
    except Exception as e:
        logger.error(f"An error occurred during regeneration for {request.matchId}: {e}", exc_info=True)
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
