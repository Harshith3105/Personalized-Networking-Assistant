import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.event_analyzer import extract_themes
from backend.topic_generator import generate_starters
from backend.fact_checker import get_fact_check
from backend.history_logger import save_conversation, save_feedback, get_history, get_feedback, init_storage

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("backend.main")

app = FastAPI(
    title="Personalized Networking Assistant API",
    description="Backend API for theme extraction, conversation generation, fact checking, and logging.",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize JSON file storage at startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing persistence storage...")
    init_storage()

# Pydantic Schemas for Requests & Responses
class AnalyzeEventRequest(BaseModel):
    event_description: str = Field(..., examples=["AI for Sustainable Cities"])
    interests: List[str] = Field(..., examples=[["climate change", "urban planning"]])

class AnalyzeEventResponse(BaseModel):
    themes: List[str]

class GenerateConversationRequest(BaseModel):
    event_description: str
    themes: List[str]
    interests: List[str]

class StarterItem(BaseModel):
    id: str
    text: str
    feedback: Optional[str] = None

class GenerateConversationResponse(BaseModel):
    id: str
    timestamp: str
    event_description: str
    interests: List[str]
    themes: List[str]
    starters: List[StarterItem]

class FactCheckRequest(BaseModel):
    query: str = Field(..., examples=["blockchain in healthcare"])

class FactCheckResponse(BaseModel):
    query: str
    title: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    success: bool
    error: Optional[str] = None

class FeedbackRequest(BaseModel):
    starter_id: str
    feedback: str = Field(..., pattern="^(up|down)$", examples=["up"])

class FeedbackResponse(BaseModel):
    success: bool
    message: str
    data: dict

# Endpoints

@app.post("/analyze-event", response_model=AnalyzeEventResponse)
def api_analyze_event(payload: AnalyzeEventRequest):
    logger.info(f"Received theme extraction request for event: {payload.event_description[:50]}...")
    if not payload.event_description.strip():
        raise HTTPException(status_code=400, detail="Event description cannot be empty")
    
    # We combine user-defined interests and some fallback generic networking concepts
    # to form the candidate labels for zero-shot classification.
    # The default themes provide context if user interests are narrow.
    default_themes = ["Technology", "Sustainability", "Innovation", "Business", "Networking", "Design"]
    candidate_labels = list(set(payload.interests + default_themes))
    
    themes = extract_themes(payload.event_description, candidate_labels)
    return AnalyzeEventResponse(themes=themes)

@app.post("/generate-conversation", response_model=GenerateConversationResponse)
def api_generate_conversation(payload: GenerateConversationRequest):
    logger.info(f"Received conversation starters request for event: {payload.event_description[:50]}...")
    if not payload.event_description.strip():
        raise HTTPException(status_code=400, detail="Event description cannot be empty")
        
    starters = generate_starters(payload.event_description, payload.themes, payload.interests)
    
    # Persist the output in local history.json
    saved_entry = save_conversation(
        event_description=payload.event_description,
        interests=payload.interests,
        themes=payload.themes,
        starters=starters
    )
    
    return GenerateConversationResponse(**saved_entry)

@app.post("/fact-check", response_model=FactCheckResponse)
def api_fact_check(payload: FactCheckRequest):
    logger.info(f"Received fact check request for: {payload.query}")
    result = get_fact_check(payload.query)
    return FactCheckResponse(**result)

@app.get("/history", response_model=List[GenerateConversationResponse])
def api_get_history():
    logger.info("Fetching conversation history logs.")
    return get_history()

@app.post("/feedback", response_model=FeedbackResponse)
def api_submit_feedback(payload: FeedbackRequest):
    logger.info(f"Received feedback action for starter {payload.starter_id}: {payload.feedback}")
    try:
        feedback_entry = save_feedback(payload.starter_id, payload.feedback)
        return FeedbackResponse(
            success=True,
            message="Feedback logged successfully.",
            data=feedback_entry
        )
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to log feedback")
