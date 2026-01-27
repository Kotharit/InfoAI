from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import pdfplumber
import tempfile
import json
import base64

# Import our prompt compiler
from compiler.prompt_compiler import compile_prompt, validate_blueprint

# Import Google GenAI SDK for both text and image generation
from google import genai
from google.genai import types

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - handle missing MONGO_URL for Vercel
mongo_url = os.environ.get('MONGO_URL', '')
db = None
if mongo_url:
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'infographic_db')]

# Initialize Google GenAI client with user's API key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Create the main app
app = FastAPI(title="Infographic Studio API", version="2.1.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure debug directory exists
DEBUG_DIR = Path("/tmp/debug")
try:
    DEBUG_DIR.mkdir(exist_ok=True)
except:
    DEBUG_DIR = Path("/tmp")

# Simple user database (in production, use proper hashing)
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "contributor": {"password": "contrib123", "role": "contributor"}
}

# In-memory usage tracking for serverless (fallback when no DB)
usage_cache = {}


def save_debug_file(filename: str, content: str):
    """Save content to debug directory."""
    try:
        filepath = DEBUG_DIR / filename
        with open(filepath, 'w') as f:
            f.write(content)
        logger.info(f"Debug file saved: {filepath}")
    except Exception as e:
        logger.error(f"Failed to save debug file {filename}: {e}")


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


def build_gemini_prompt(document_text: str, settings: Dict[str, Any]) -> str:
    """Build the Gemini prompt with user settings."""
    
    layout = settings.get("layout", "before_after_with_recommendations")
    creativity = settings.get("creativity", "moderate")
    palette = settings.get("palette", "teal")
    text_density = settings.get("textDensity", "balanced")
    tone = settings.get("tone", "professional")
    
    tone_mapping = {
        "professional": "professional",
        "creative": "executive"
    }
    json_tone = tone_mapping.get(tone, "professional")
    
    text_instructions = {
        "low": "Use minimal text. Focus on visual elements and icons. Each bullet point should be 3-5 words max.",
        "balanced": "Balance text and visuals. Each bullet point should be 6-10 words.",
        "high": "Include detailed text. Each bullet point can be 10-15 words with more context."
    }
    text_instruction = text_instructions.get(text_density, text_instructions["balanced"])
    
    tone_instructions = {
        "professional": "Maintain a formal, business-appropriate tone. Focus on clarity and precision.",
        "creative": "Use engaging, storytelling language. Be more expressive and use vivid metaphors."
    }
    tone_instruction = tone_instructions.get(tone, tone_instructions["professional"])
    
    prompt = f'''You are a document understanding assistant. Your ONLY job is to read the provided professional report text and output a single VALID JSON object following the exact Visual Blueprint Schema provided. DO NOT output any explanation, commentary, HTML, or image prompts. Output MUST be valid JSON and conform strictly to schema.

Report text:
<<START>>
{document_text}
<<END>>

USER PREFERENCES:
- Preferred Layout: {layout}
- Creativity Level: {creativity}
- Color Palette: {palette}
- Text Density: {text_density} - {text_instruction}
- Tone: {tone} - {tone_instruction}

TASK:
- Understand the report's structure, intent, and decision points.
- Identify: (1) problems/risk (before), (2) actions taken (after), (3) findings, (4) clear recommendations, (5) outcomes.
- Produce "summary" (1-2 sentences) and populate "sections" using types: before_after, findings_actions, recommendations, outcome.
- Use the preferred layout: "{layout}"
- Set creativity to: "{creativity}"
- Use palette: "{palette}"
- Set tone to: "{json_tone}"
- Use "visual_metaphor" to suggest imagery or metaphors for each section (short phrases only, max 10 words).
- Return EXACTLY the JSON object and NOTHING ELSE.

REQUIRED JSON SCHEMA:
{{
  "title": "string (max 100 chars)",
  "subtitle": "string (max 150 chars)",
  "summary": "string (1-2 sentences, max 300 chars)",
  "tone": "professional" | "executive" | "technical",
  "creativity": "{creativity}",
  "layout": "{layout}",
  "palette": "{palette}",
  "sections": [
    {{
      "id": "string",
      "type": "before_after" | "findings_actions" | "recommendations" | "outcome" | "metric",
      "heading": "string (max 80 chars)",
      "before": ["string"],
      "after": ["string"],
      "findings": ["string"],
      "actions": ["string"],
      "items": ["string"],
      "points": ["string"],
      "visual_metaphor": "string (max 50 chars)",
      "metaphor_direction": "left_vs_right" | "top_vs_bottom" | "overlay",
      "emphasis": "low" | "medium" | "high"
    }}
  ]
}}

IMPORTANT: Return EXACTLY the JSON object and NOTHING ELSE. No markdown, no code blocks, no explanation.'''
    
    return prompt


async def call_gemini_for_blueprint(input_text: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Call Gemini API to generate Visual Blueprint JSON with user settings."""
    if not genai_client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    prompt = build_gemini_prompt(input_text, settings)
    
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
        )
        
        response_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                response_text += part.text
        
        logger.info(f"Gemini raw response (first 500 chars): {response_text[:500]}...")
        save_debug_file("raw_model_output.txt", response_text)
        
        return {"text": response_text}
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")


async def call_nano_banana_for_image(compiled_prompt: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Call Nano Banana (Gemini Image) API to generate infographic image using user's Gemini API key."""
    if not genai_client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    # Critical text-minimization instructions
    text_rules = """

=== CRITICAL INSTRUCTIONS FOR ERROR-FREE OUTPUT ===
⚠️ TEXT RENDERING RULES - FOLLOW STRICTLY:

1. MINIMIZE ALL TEXT - Text in images causes spelling errors
2. Use ICONS, ILLUSTRATIONS, and VISUAL METAPHORS instead of words
3. Maximum text allowed:
   - Title: Yes (keep short)
   - Subtitle: Yes (keep short)  
   - Section labels: 1-2 words ONLY (e.g., "BEFORE", "AFTER", "FINDINGS")
   - Item labels: 1 word MAX or use icons instead

4. NEVER include:
   - Bullet point lists with text
   - Paragraphs or sentences
   - Detailed descriptions as text
   - Any text longer than 3 words (except title/subtitle)

5. INSTEAD of text, use:
   - Icons and symbols (checkmarks, warning signs, arrows)
   - Illustrations showing the concept
   - Color coding to differentiate
   - Visual metaphors (tangled vs organized, broken vs fixed)
   - Charts/graphs for data

6. If you MUST include a label, use only:
   - Single common words (no complex terms)
   - ALL CAPS for clarity
   - Large, simple font

THIS IS CRITICAL: Spelling errors occur when too much text is rendered.
Keep text to an absolute minimum and let visuals tell the story.
"""
    
    text_density = settings.get("textDensity", "balanced")
    density_modifier = ""
    if text_density == "low":
        density_modifier = "\n\n⚠️ USER SELECTED 'LOW TEXT': Use ZERO text except title. All content must be purely visual - icons, illustrations, and imagery only."
    elif text_density == "high":
        density_modifier = "\n\n⚠️ USER SELECTED 'HIGH TEXT': You may include more labels, but still keep each label to 2-3 words maximum. NO sentences or paragraphs."
    else:
        density_modifier = "\n\n⚠️ USER SELECTED 'BALANCED': Minimal text labels (1-2 words each). Focus on visual communication."
    
    final_prompt = compiled_prompt + text_rules + density_modifier
    
    try:
        # Use Nano Banana Pro model
        response = genai_client.models.generate_content(
            model="nano-banana-pro-preview",
            contents=[final_prompt],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
            )
        )
        
        images = []
        text_response = ""
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_response += part.text
            elif hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/png"
                
                if isinstance(image_data, bytes):
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                else:
                    image_base64 = image_data
                
                images.append({
                    "data": image_base64,
                    "mime_type": mime_type
                })
        
        logger.info(f"Nano Banana Pro response - text: {text_response[:100] if text_response else 'None'}...")
        logger.info(f"Nano Banana Pro generated {len(images)} image(s)")
        
        debug_info = {
            "text_response": text_response[:500] if text_response else None,
            "num_images": len(images),
            "image_types": [img.get('mime_type') for img in images]
        }
        save_debug_file("nanobanana_response.json", json.dumps(debug_info, indent=2))
        
        return {
            "text": text_response,
            "images": images
        }
    except Exception as e:
        logger.error(f"Nano Banana Pro API error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Image generation failed: {str(e)}")


def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse JSON from the model response, handling markdown code blocks."""
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
    except json.JSONDecodeError:
        pass
    
    try:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = cleaned[start:end+1]
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        raise ValueError(f"Invalid JSON: {str(e)}")
    
    raise ValueError("Could not extract valid JSON from response")


# Auth Models
class LoginRequest(BaseModel):
    username: str
    password: str


# Auth Routes
@api_router.post("/auth/login")
async def login(request: LoginRequest):
    """Simple login endpoint."""
    user = USERS.get(request.username)
    if not user or user["password"] != request.password:
        return JSONResponse(
            status_code=401,
            content={"ok": False, "error": "Invalid username or password"}
        )
    
    return {
        "ok": True,
        "user": {
            "username": request.username,
            "role": user["role"]
        }
    }


@api_router.get("/auth/usage/{username}")
async def get_usage(username: str):
    """Get usage count for a user."""
    # Try MongoDB first, fallback to in-memory cache
    if db is not None:
        usage_doc = await db.usage.find_one({"username": username})
        usage_count = usage_doc.get("count", 0) if usage_doc else 0
    else:
        usage_count = usage_cache.get(username, 0)
    return {"ok": True, "usage_count": usage_count}


async def increment_usage(username: str):
    """Increment usage count for a user."""
    if db is not None:
        await db.usage.update_one(
            {"username": username},
            {"$inc": {"count": 1}},
            upsert=True
        )
    else:
        usage_cache[username] = usage_cache.get(username, 0) + 1


# Main Routes
@api_router.get("/")
async def root():
    return {"message": "Infographic Studio API", "version": "2.1.0"}


@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "2.1.0", 
        "gemini_key_configured": bool(GEMINI_API_KEY),
        "database_connected": db is not None
    }


@api_router.post("/generate")
async def generate_infographic(
    file: Optional[UploadFile] = File(None),
    prompt: Optional[str] = Form(None),
    settings: Optional[str] = Form("{}"),
    username: Optional[str] = Form("")
):
    """Generate an infographic from PDF file or text prompt with user settings."""
    user_text = (prompt or "").strip()
    temp_path = None
    
    # Parse settings
    try:
        settings_dict = json.loads(settings) if settings else {}
    except json.JSONDecodeError:
        settings_dict = {}
    
    # Check usage for contributors
    if username:
        user = USERS.get(username)
        if user and user["role"] == "contributor":
            if db:
                usage_doc = await db.usage.find_one({"username": username})
                usage_count = usage_doc.get("count", 0) if usage_doc else 0
            else:
                usage_count = usage_cache.get(username, 0)
            if usage_count >= 2:
                return JSONResponse(
                    status_code=403,
                    content={"ok": False, "error": "Usage limit reached. Contact admin for more access."}
                )
    
    try:
        # Step 1: Handle PDF file upload
        if file and file.filename:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            extracted_text = extract_text_from_pdf(temp_path)
            if extracted_text:
                user_text = (user_text + "\n\n" + extracted_text) if user_text else extracted_text
        
        if not user_text:
            raise HTTPException(status_code=400, detail="No text or file provided")
        
        input_text = prepare_payload_text(user_text)
        logger.info(f"Processing input text of length: {len(input_text)}")
        logger.info(f"Settings: {settings_dict}")
        
        # Step 2: Call Gemini for Visual Blueprint with settings
        logger.info("Calling Gemini for Visual Blueprint...")
        gemini_response = await call_gemini_for_blueprint(input_text, settings_dict)
        raw_text = gemini_response.get("text", "")
        
        # Step 3: Parse and validate blueprint
        try:
            blueprint = parse_json_response(raw_text)
        except ValueError as e:
            save_debug_file("raw_model_output.txt", raw_text)
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": "Model output not valid JSON", "raw": raw_text[:2000]}
            )
        
        save_debug_file("blueprint.json", json.dumps(blueprint, indent=2))
        
        is_valid, error_msg = validate_blueprint(blueprint)
        if not is_valid:
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": f"Blueprint validation failed: {error_msg}", "blueprint": blueprint}
            )
        
        # Step 4: Compile blueprint into Nano Banana prompt
        logger.info("Compiling blueprint into Nano Banana prompt...")
        compiled_prompt = compile_prompt(blueprint)
        save_debug_file("compiled_prompt.txt", compiled_prompt)
        logger.info(f"Compiled prompt length: {len(compiled_prompt)} chars")
        
        # Step 5: Call Nano Banana Pro for image generation
        logger.info("Calling Nano Banana Pro for image generation...")
        image_response = await call_nano_banana_for_image(compiled_prompt, settings_dict)
        
        images = image_response.get("images", [])
        if not images:
            return JSONResponse(
                status_code=502,
                content={"ok": False, "error": "No image generated"}
            )
        
        # Increment usage for the user
        if username:
            await increment_usage(username)
        
        image_data = images[0]
        image_base64 = image_data.get("data", "")
        mime_type = image_data.get("mime_type", "image/png")
        
        return {
            "ok": True,
            "blueprint": blueprint,
            "image": {
                "data": image_base64,
                "mime_type": mime_type
            },
            "compiled_prompt_preview": compiled_prompt[:500] + "..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@api_router.get("/debug/blueprint")
async def get_debug_blueprint():
    """Get the last generated blueprint for debugging."""
    try:
        filepath = DEBUG_DIR / "blueprint.json"
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return {"error": "No blueprint found"}
    except Exception as e:
        return {"error": str(e)}


@api_router.get("/debug/prompt")
async def get_debug_prompt():
    """Get the last compiled prompt for debugging."""
    try:
        filepath = DEBUG_DIR / "compiled_prompt.txt"
        if filepath.exists():
            with open(filepath, 'r') as f:
                return {"prompt": f.read()}
        return {"error": "No compiled prompt found"}
    except Exception as e:
        return {"error": str(e)}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# For Vercel serverless
handler = app
