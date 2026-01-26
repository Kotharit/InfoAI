from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import pdfplumber
import tempfile
import json
import base64

# Import our prompt compiler
from compiler.prompt_compiler import compile_prompt, validate_blueprint

# Import Google GenAI SDK
from google import genai
from google.genai import types

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize Google GenAI client
genai_client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY', ''))

# Create the main app without a prefix
app = FastAPI(title="Infographic MVP API", version="2.0.0")

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
DEBUG_DIR.mkdir(exist_ok=True)


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


# Gemini system prompt for Visual Blueprint generation
GEMINI_BLUEPRINT_PROMPT = '''You are a document understanding assistant. Your ONLY job is to read the provided professional report text and output a single VALID JSON object following the exact Visual Blueprint Schema provided. DO NOT output any explanation, commentary, HTML, or image prompts. Output MUST be valid JSON and conform strictly to schema.

Report text:
<<START>>
{document_text}
<<END>>

TASK:
- Understand the report's structure, intent, and decision points.
- Identify: (1) problems/risk (before), (2) actions taken (after), (3) findings, (4) clear recommendations, (5) outcomes.
- Produce "summary" (1-2 sentences) and populate "sections" using types: before_after, findings_actions, recommendations, outcome.
- Choose a "layout" suggestion (one of: before_after_with_recommendations, split_two_column, process_flow, summary_grid) that best fits the report.
- Set "creativity" to one of: none, subtle, moderate, high — based on how metaphorical or storytelling-oriented the visual can be.
- Use "visual_metaphor" to suggest imagery or metaphors for each section (short phrases only, max 10 words).
- Keep each text item concise (≤12 words).
- Return EXACTLY the JSON object and NOTHING ELSE.

REQUIRED JSON SCHEMA:
{{
  "title": "string (max 100 chars)",
  "subtitle": "string (max 150 chars)",
  "summary": "string (1-2 sentences, max 300 chars)",
  "tone": "professional" | "executive" | "technical",
  "creativity": "none" | "subtle" | "moderate" | "high",
  "layout": "before_after_with_recommendations" | "split_two_column" | "process_flow" | "summary_grid",
  "palette": "teal" | "warm" | "mono",
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


async def call_gemini_for_blueprint(input_text: str) -> Dict[str, Any]:
    """Call Gemini API to generate Visual Blueprint JSON."""
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    prompt = GEMINI_BLUEPRINT_PROMPT.format(document_text=input_text)
    
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
        )
        
        # Get the text response
        response_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                response_text += part.text
        
        logger.info(f"Gemini raw response (first 500 chars): {response_text[:500]}...")
        
        # Save raw response for debugging
        save_debug_file("raw_model_output.txt", response_text)
        
        return {"text": response_text}
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")


async def call_nano_banana_for_image(compiled_prompt: str) -> Dict[str, Any]:
    """Call Nano Banana (Gemini Image) API to generate infographic image."""
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    try:
        # Use Nano Banana (gemini-2.5-flash-image) for image generation
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[compiled_prompt],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio="3:2",  # Landscape for infographics
                )
            )
        )
        
        images = []
        text_response = ""
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_response += part.text
            elif hasattr(part, 'inline_data') and part.inline_data:
                # Get base64 image data
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/png"
                
                # Convert to base64 string if it's bytes
                if isinstance(image_data, bytes):
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                else:
                    image_base64 = image_data
                
                images.append({
                    "data": image_base64,
                    "mime_type": mime_type
                })
        
        logger.info(f"Nano Banana response - text: {text_response[:100] if text_response else 'None'}...")
        logger.info(f"Nano Banana generated {len(images)} image(s)")
        
        # Save response metadata for debugging
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
        logger.error(f"Nano Banana API error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"Image generation failed: {str(e)}")


def parse_json_response(text: str) -> Dict[str, Any]:
    """Parse JSON from the model response, handling markdown code blocks."""
    
    # Clean up the response
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    # First try direct parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON object using brace matching
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


# Routes
@api_router.get("/")
async def root():
    return {"message": "Infographic MVP API v2.0 - Gemini Blueprint → Nano Banana Pipeline (Your API Key)"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0", "api_key_configured": bool(os.environ.get('GEMINI_API_KEY'))}


@api_router.post("/generate")
async def generate_infographic(
    file: Optional[UploadFile] = File(None),
    prompt: Optional[str] = Form(None)
):
    """
    Generate an infographic from PDF file or text prompt.
    
    Pipeline:
    1. Extract text from PDF/prompt
    2. Call Gemini to generate Visual Blueprint JSON
    3. Validate blueprint against schema
    4. Compile blueprint into Nano Banana prompt
    5. Call Nano Banana to generate image
    6. Return image as base64
    """
    user_text = (prompt or "").strip()
    temp_path = None
    
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
        
        # Prepare and trim input
        input_text = prepare_payload_text(user_text)
        logger.info(f"Processing input text of length: {len(input_text)}")
        
        # Step 2: Call Gemini for Visual Blueprint
        logger.info("Calling Gemini for Visual Blueprint...")
        gemini_response = await call_gemini_for_blueprint(input_text)
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
        
        # Save valid blueprint
        save_debug_file("blueprint.json", json.dumps(blueprint, indent=2))
        
        # Validate blueprint
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
        
        # Step 5: Call Nano Banana for image generation
        logger.info("Calling Nano Banana for image generation...")
        image_response = await call_nano_banana_for_image(compiled_prompt)
        
        images = image_response.get("images", [])
        if not images:
            return JSONResponse(
                status_code=502,
                content={"ok": False, "error": "No image generated by Nano Banana"}
            )
        
        # Get the first image
        image_data = images[0]
        image_base64 = image_data.get("data", "")
        mime_type = image_data.get("mime_type", "image/png")
        
        # Return success response
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
        # Clean up temp file
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
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
