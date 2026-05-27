import os
import time
import json
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.retriever import SchemeRetriever
from rag.generator import AnswerGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global instances of ML models
retriever = None
generator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize retriever and generator once at startup.
    This avoids the expensive operation of loading the model per request.
    """
    global retriever, generator
    print("Starting up: Initializing ML models...")
    
    try:
        retriever = SchemeRetriever()
        print("Retriever loaded successfully.")
    except Exception as e:
        print(f"Retriever not ready: {e}")
        retriever = None

    try:
        generator = AnswerGenerator()
        print("Generator loaded successfully.")
    except Exception as e:
        print(f"Generator not ready: {e}")
        generator = None
        
    print("Startup complete.")
    yield
    print("Shutting down Sarkari Saathi API...")

app = FastAPI(
    title="Sarkari Saathi RAG API",
    description="RAG-powered scheme matching for Indian citizens",
    version="1.0.0",
    lifespan=lifespan
)

# Port configuration
port = int(os.getenv("PORT", 8000))

# CORS configuration allowing local dev and Vercel prod
allow_origins = ["https://sarkari-saathi-five.vercel.app"]
if os.getenv("ENVIRONMENT") == "development":
    allow_origins = ["*", "http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# --- Pydantic Models for Validation ---
class UserProfile(BaseModel):
    situation: str
    education: str
    location: str
    has_phone: bool = True
    target_earning: str = "any"

class MatchRequest(BaseModel):
    profile: UserProfile
    lang: str = Field(default="en", description="Language preference: 'hi' or 'en'")

class FeedbackRequest(BaseModel):
    profile: dict
    selected_scheme_id: str
    helpful: bool

# --- API Routes ---

@app.get("/test")
async def test_api():
    """Quick testing route to check if API is working and retriever is ready."""
    return {
        "message": "API working",
        "retriever_ready": retriever is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/match-schemes")
async def match_schemes(request: MatchRequest):
    """
    Core RAG Endpoint:
    1. Validates profile
    2. Retrieves top schemes from ChromaDB
    3. Generates personalized explanation with Gemini
    4. Returns JSON response with timings
    """
    if retriever is None or generator is None:
        # Fallback local data if models aren't ready
        return {
            "schemes": [
                {
                    "id": "fallback_1",
                    "name_hi": "प्रधानमंत्री कौशल विकास योजना",
                    "name_en": "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
                    "benefit_hi": "मुफ़्त कौशल प्रशिक्षण और प्रमाणन",
                    "benefit_en": "Free Skill Training & Certification",
                    "why_relevant_hi": "यह योजना आपके प्रोफाइल के आधार पर कौशल और रोजगार प्राप्त करने में मदद कर सकती है।",
                    "why_relevant_en": "This scheme can help you gain skills and employment based on your profile.",
                    "documents_needed": ["Aadhaar Card", "Bank Account Details"],
                    "apply_link": "https://www.pmkvyofficial.org/",
                    "priority": "high"
                }
            ],
            "earning_opportunities": [],
            "total_schemes_searched": 0,
            "retrieval_time_ms": 0,
            "generation_time_ms": 0,
            "personalized_message": "Our AI backend is currently warming up or pending setup. Here is a recommended scheme for you in the meantime!"
        }
    
    try:
        # Step 2: Semantic Retrieval
        t0 = time.time()
        docs = retriever.retrieve(request.profile.model_dump(), top_k=10)
        t_retrieval_ms = (time.time() - t0) * 1000

        # Step 3: Generative AI Explanation
        t1 = time.time()
        gen_output = generator.generate(request.profile.model_dump(), docs, request.lang)
        t_gen_ms = (time.time() - t1) * 1000
        
        # Pick the personalized message based on requested language
        msg_key = f"personalized_message_{request.lang}"
        
        # Step 4: Return Response
        return {
            "schemes": gen_output.get("schemes", []),
            "earning_opportunities": gen_output.get("earning_opportunities", []),
            "total_schemes_searched": retriever.get_collection_size(),
            "retrieval_time_ms": round(t_retrieval_ms),
            "generation_time_ms": round(t_gen_ms),
            "personalized_message": gen_output.get(msg_key, "")
        }
    except Exception as e:
        print(f"Error processing /match-schemes request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during matching.")

@app.get("/health")
async def health():
    try:
        count = retriever.get_collection_size() if retriever else 0
        model_ready = retriever is not None
    except:
        count = 0
        model_ready = False
    
    return {
        "status": "ok",
        "schemes_indexed": count,
        "model_loaded": model_ready,
        "version": "1.0.0"
    }
@app.get("/stats")
async def stats():
    """Returns general statistics about the scheme database."""
    if not retriever:
        raise HTTPException(status_code=503, detail="Database connection pending.")
        
    return {
        "total_schemes": retriever.get_collection_size(),
        "states_covered": 28,       # Placeholder, can be aggregated from DB later
        "ministries_covered": 45,   # Placeholder
        "last_updated": datetime.now().isoformat()
    }

@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    """Saves user feedback for future fine-tuning."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "selected_scheme_id": req.selected_scheme_id,
        "helpful": req.helpful,
        "profile": req.profile
    }
    
    log_file = os.path.join(os.path.dirname(__file__), "feedback.log")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Failed to log feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback.")
        
    return {"status": "success", "message": "Feedback recorded"}
