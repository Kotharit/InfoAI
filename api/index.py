from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import json
import base64
import tempfile
import logging

# Import Google GenAI SDK
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Infographic Studio API", version="2.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
genai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Simple user database
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "contributor": {"password": "contrib123", "role": "contributor"}
}

# In-memory usage tracking (resets on cold start)
usage_cache = {}

# Prompt Compiler (simplified inline version)
def compile_prompt(blueprint: Dict[str, Any]) -> str:
    """Compile Visual Blueprint into Nano Banana prompt."""
    title = blueprint.get("title", "Untitled")
    subtitle = blueprint.get("subtitle", "")
    creativity = blueprint.get("creativity", "moderate")
    palette = blueprint.get("palette", "teal")
    layout = blueprint.get("layout", "before_after_with_recommendations")
    sections = blueprint.get("sections", [])
    
    palette_colors = {
        "teal": "#0d9488",
        "warm": "#ea580c",
        "mono": "#374151"
    }
    
    sections_text = ""
    for i, section in enumerate(sections, 1):
        heading = section.get("heading", f"Section {i}")
        section_type = section.get("type", "outcome")
        metaphor = section.get("visual_metaphor", "")
        
        if section_type == "before_after":
            before = section.get("before", [])
            after = section.get("after", [])
            sections_text += f"""
Section {i}: {heading} (Before/After)
- LEFT (BEFORE): Show chaotic state - {', '.join(before[:2]) if before else 'problems'}
- RIGHT (AFTER): Show organized state - {', '.join(after[:2]) if after else 'solutions'}
- Visual metaphor: {metaphor}
"""
        elif section_type == "recommendations":
            items = section.get("items", [])
            sections_text += f"""
Section {i}: {heading} (Recommendations)
- Show as checkmark icons with 1-word labels
- Items: {', '.join(items[:3]) if items else 'key recommendations'}
"""
        else:
            points = section.get("points", section.get("findings", section.get("actions", [])))
            sections_text += f"""
Section {i}: {heading}
- Show as icons/illustrations
- Key points: {', '.join(points[:3]) if points else 'key information'}
"""

    prompt = f"""Create a professional infographic image.

CRITICAL: MINIMIZE TEXT - Use icons and illustrations instead of words!

Title: "{title}"
Subtitle: "{subtitle}"

Style:
- Layout: {layout}
- Creativity: {creativity}
- Color: {palette_colors.get(palette, '#0d9488')}
- Typography: Clean sans-serif, minimal text

Sections:
{sections_text}

RULES:
- Maximum 1-3 words per label
- NO paragraphs or sentences
- Use icons, illustrations, visual metaphors
- Title and subtitle are the only full text
"""
    return prompt


def build_gemini_prompt(document_text: str, settings: Dict[str, Any]) -> str:
    """Build Gemini prompt for blueprint generation."""
    layout = settings.get("layout", "before_after_with_recommendations")
    creativity = settings.get("creativity", "moderate")
    palette = settings.get("palette", "teal")
    
    return f'''Output a single valid JSON object for an infographic blueprint. NO explanation, NO markdown.

Report:
{document_text[:10000]}

Requirements:
- Layout: {layout}
- Creativity: {creativity}
- Palette: {palette}

JSON Schema:
{{
  "title": "string",
  "subtitle": "string",
  "summary": "string",
  "tone": "professional",
  "creativity": "{creativity}",
  "layout": "{layout}",
  "palette": "{palette}",
  "sections": [
    {{
      "id": "string",
      "type": "before_after|findings_actions|recommendations|outcome",
      "heading": "string",
      "before": ["string"],
      "after": ["string"],
      "findings": ["string"],
      "actions": ["string"],
      "items": ["string"],
      "points": ["string"],
      "visual_metaphor": "string",
      "emphasis": "low|medium|high"
    }}
  ]
}}

Return ONLY the JSON object.'''


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api")
async def root():
    return {"message": "Infographic Studio API", "version": "2.1.0"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "gemini_configured": bool(GEMINI_API_KEY)}


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    user = USERS.get(request.username)
    if not user or user["password"] != request.password:
        return JSONResponse(status_code=401, content={"ok": False, "error": "Invalid credentials"})
    return {"ok": True, "user": {"username": request.username, "role": user["role"]}}


@app.get("/api/auth/usage/{username}")
async def get_usage(username: str):
    return {"ok": True, "usage_count": usage_cache.get(username, 0)}


@app.post("/api/generate")
async def generate(
    file: Optional[UploadFile] = File(None),
    prompt: Optional[str] = Form(None),
    settings: Optional[str] = Form("{}"),
    username: Optional[str] = Form("")
):
    if not genai_client:
        return JSONResponse(status_code=500, content={"ok": False, "error": "GEMINI_API_KEY not configured"})
    
    # Parse settings
    try:
        settings_dict = json.loads(settings) if settings else {}
    except:
        settings_dict = {}
    
    # Check usage
    if username:
        user = USERS.get(username)
        if user and user["role"] == "contributor" and usage_cache.get(username, 0) >= 2:
            return JSONResponse(status_code=403, content={"ok": False, "error": "Usage limit reached"})
    
    user_text = (prompt or "").strip()
    
    # Handle PDF
    if file and file.filename and file.filename.lower().endswith('.pdf'):
        try:
            import pdfplumber
            content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        user_text += "\n" + text
            os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"PDF error: {e}")
    
    if not user_text:
        return JSONResponse(status_code=400, content={"ok": False, "error": "No text provided"})
    
    try:
        # Step 1: Generate blueprint
        gemini_prompt = build_gemini_prompt(user_text, settings_dict)
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[gemini_prompt]
        )
        
        raw_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                raw_text += part.text
        
        # Parse JSON
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            blueprint = json.loads(cleaned[start:end+1])
        else:
            return JSONResponse(status_code=500, content={"ok": False, "error": "Invalid JSON", "raw": raw_text[:500]})
        
        # Step 2: Compile prompt
        compiled_prompt = compile_prompt(blueprint)
        
        # Step 3: Generate image
        text_density = settings_dict.get("textDensity", "balanced")
        text_rule = "\n\nCRITICAL: Use ICONS and ILLUSTRATIONS instead of text. Maximum 1-2 word labels only!"
        if text_density == "low":
            text_rule = "\n\nCRITICAL: NO TEXT except title. Pure visual icons and illustrations only!"
        
        image_response = genai_client.models.generate_content(
            model="nano-banana-pro-preview",
            contents=[compiled_prompt + text_rule],
            config=types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])
        )
        
        images = []
        for part in image_response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                data = part.inline_data.data
                if isinstance(data, bytes):
                    data = base64.b64encode(data).decode('utf-8')
                images.append({"data": data, "mime_type": part.inline_data.mime_type or "image/png"})
        
        if not images:
            return JSONResponse(status_code=502, content={"ok": False, "error": "No image generated"})
        
        # Increment usage
        if username:
            usage_cache[username] = usage_cache.get(username, 0) + 1
        
        return {
            "ok": True,
            "blueprint": blueprint,
            "image": images[0],
            "compiled_prompt_preview": compiled_prompt[:300] + "..."
        }
        
    except Exception as e:
        logger.error(f"Generate error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


# Vercel handler
handler = app
