from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import pdfplumber
import tempfile
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class InfographicBlock(BaseModel):
    id: int
    icon: str
    heading: str
    bullets: List[str]

class InfographicStyle(BaseModel):
    palette: str

class InfographicData(BaseModel):
    title: str
    subtitle: str
    layout: str
    style: InfographicStyle
    blocks: List[InfographicBlock]

class GenerateResponse(BaseModel):
    ok: bool
    infographic: Optional[InfographicData] = None
    error: Optional[str] = None
    raw: Optional[str] = None

# Helper functions
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")
    return text.strip()

def prepare_payload_text(input_text: str, max_length: int = 15000) -> str:
    """Trim input text to maximum length."""
    if not input_text:
        return ""
    return input_text[:max_length] if len(input_text) > max_length else input_text

async def call_gemini_for_infographic(input_text: str) -> dict:
    """Call Gemini API to generate infographic JSON."""
    api_key = os.environ.get('EMERGENT_LLM_KEY', '')
    if not api_key:
        raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")
    
    prompt = f"""SYSTEM: You are an assistant that MUST output a single valid JSON object and NOTHING ELSE. The JSON will describe an infographic for direct rendering. Follow the JSON schema exactly.

USER INPUT: 
<<START USER CONTENT>>
{input_text}
<<END USER CONTENT>>

TASK: Extract one title, a one-line subtitle, choose a layout from ["vertical_steps","timeline","grid"], pick a palette from ["teal","warm","mono"], and produce between 3 and 6 content blocks. Each block must have an integer id, an icon keyword (single word), a short heading (3–6 words), and 1–3 bullets (each ≤10 words). Keep everything concise. Do NOT include any commentary or extra fields.

REQUIRED JSON SCHEMA (exact):
{{
  "title": string,
  "subtitle": string,
  "layout": "vertical_steps"|"timeline"|"grid",
  "style": {{ "palette": "teal"|"warm"|"mono" }},
  "blocks": [
    {{ "id": integer, "icon": string, "heading": string, "bullets": [string] }}
  ]
}}

IMPORTANT: Return EXACTLY the JSON object and nothing else. No markdown code blocks, no explanation, just the raw JSON."""

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="You are a JSON-only response assistant. You must always respond with valid JSON and nothing else."
        )
        chat.with_model("gemini", "gemini-2.5-flash")
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        logger.info(f"Gemini raw response: {response[:500]}...")
        return {"text": response}
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

def parse_json_response(text: str) -> dict:
    """Parse JSON from the model response, handling markdown code blocks."""
    import json
    
    # Clean up the response - remove markdown code blocks if present
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}, text: {cleaned[:200]}")
        raise ValueError(f"Invalid JSON: {str(e)}")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Infographic MVP API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

@api_router.post("/generate")
async def generate_infographic(
    file: Optional[UploadFile] = File(None),
    prompt: Optional[str] = Form(None)
):
    """
    Generate an infographic from PDF file or text prompt.
    Accepts multipart/form-data with optional 'file' (PDF) and 'prompt' (text).
    """
    user_text = (prompt or "").strip()
    temp_path = None
    
    try:
        # Handle PDF file upload
        if file and file.filename:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(temp_path)
            if extracted_text:
                user_text = (user_text + "\n\n" + extracted_text) if user_text else extracted_text
        
        if not user_text:
            raise HTTPException(status_code=400, detail="No text or file provided")
        
        # Prepare and trim input
        input_text = prepare_payload_text(user_text)
        logger.info(f"Processing input text of length: {len(input_text)}")
        
        # Call Gemini API
        response = await call_gemini_for_infographic(input_text)
        raw_text = response.get("text", "")
        
        # Parse JSON response
        try:
            parsed = parse_json_response(raw_text)
        except ValueError as e:
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": "Model output not valid JSON", "raw": raw_text}
            )
        
        # Validate required fields
        if not parsed.get("title") or not isinstance(parsed.get("blocks"), list):
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": "Parsed JSON missing required fields", "parsed": parsed}
            )
        
        return {"ok": True, "infographic": parsed}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
