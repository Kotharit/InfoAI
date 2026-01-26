"""
Prompt Compiler - Deterministic conversion of Visual Blueprint JSON to Nano Banana Pro prompt.
This module contains NO stochastic/AI steps - purely rule-based transformation.
"""

import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Palette mappings
PALETTE_DEFINITIONS = {
    "teal": {
        "primary": "#0d9488",
        "secondary": "#14b8a6",
        "accent": "#2dd4bf",
        "background": "#f0fdfa",
        "dark": "#134e4a",
        "description": "teal/cyan/blue-green professional palette"
    },
    "warm": {
        "primary": "#ea580c",
        "secondary": "#f97316",
        "accent": "#fb923c",
        "background": "#fff7ed",
        "dark": "#9a3412",
        "description": "warm orange/amber professional palette"
    },
    "mono": {
        "primary": "#374151",
        "secondary": "#6b7280",
        "accent": "#9ca3af",
        "background": "#f9fafb",
        "dark": "#111827",
        "description": "monochrome grey professional palette"
    }
}

# Layout templates
LAYOUT_INSTRUCTIONS = {
    "before_after_with_recommendations": """
Layout: BEFORE/AFTER with RECOMMENDATIONS structure
- Left side (40%): BEFORE state - show problems, chaos, issues with warning visual cues
- Right side (40%): AFTER state - show solutions, order, improvements with success visual cues
- Bottom section (20%): RECOMMENDATIONS callout box with check icons and action items
- Use clear visual separation between before/after with a dividing line or gradient transition
- Include small labels "BEFORE" and "AFTER" above respective sections
""",
    "split_two_column": """
Layout: TWO-COLUMN SPLIT structure
- Left column (50%): Primary information, findings, or current state
- Right column (50%): Secondary information, actions, or recommendations
- Consistent vertical alignment between columns
- Use visual connectors or arrows to show relationships
""",
    "process_flow": """
Layout: PROCESS FLOW structure
- Horizontal or vertical flow from start to end
- Each step in a distinct container with number or icon
- Connecting arrows or lines between steps
- Progressive visual treatment (lighter to darker, or left to right)
""",
    "summary_grid": """
Layout: SUMMARY GRID structure
- 2x2 or 2x3 grid of equal-sized sections
- Each section has icon, heading, and bullet points
- Consistent styling across all grid cells
- Clear grid lines or spacing for visual separation
"""
}

# Creativity modifiers
CREATIVITY_MODIFIERS = {
    "none": {
        "style": "literal, documentary, factual",
        "metaphors": "NO metaphors or symbolic imagery. Use only literal representations.",
        "restrictions": "Strictly informational. No artistic flourishes."
    },
    "subtle": {
        "style": "professional with minor symbolic touches",
        "metaphors": "Use subtle, tasteful symbolism. Minor metaphorical elements that enhance understanding.",
        "restrictions": "Keep metaphors minimal and clearly business-appropriate."
    },
    "moderate": {
        "style": "storytelling-oriented with clear metaphors",
        "metaphors": "Include clear visual metaphors and illustrative storytelling elements. Transform concepts into relatable visual narratives.",
        "restrictions": "Balance creativity with professionalism. Metaphors should enhance, not obscure meaning."
    },
    "high": {
        "style": "highly metaphorical, stylized storytelling",
        "metaphors": "Strong metaphorical scenes with artistic interpretation. Transform data into compelling visual stories.",
        "restrictions": "EXPERIMENTAL: Maintain executive clarity despite creative styling. Avoid gimmicks."
    }
}

# Section type templates - VISUAL-FOCUSED (minimal text)
SECTION_TEMPLATES = {
    "before_after": """
{heading} Section (Before/After Visual Comparison):
  ⚠️ USE ILLUSTRATIONS NOT TEXT for this section
  
  LEFT (BEFORE) - Create an ILLUSTRATION showing:
    - Visual scene depicting: {before_visual}
    - Single word label: "BEFORE"
    - Show through imagery: {before_items}
    - Visual mood: Chaotic, messy, problematic (use visual cues like tangled elements, warning colors)
    {metaphor_before}
  
  RIGHT (AFTER) - Create an ILLUSTRATION showing:
    - Visual scene depicting: {after_visual}
    - Single word label: "AFTER"  
    - Show through imagery: {after_items}
    - Visual mood: Organized, clean, resolved (use visual cues like neat arrangements, success colors)
    {metaphor_after}
  
  Emphasis: {emphasis}
  DO NOT write out the items as text - DRAW them as illustrations
""",
    "findings_actions": """
{heading} Section (Visual Findings → Actions):
  ⚠️ USE ICONS AND SYMBOLS NOT TEXT
  
  FINDINGS (left/top) - Show with ICONS:
    - Use magnifying glass or observation icons
    - Represent each finding with a simple icon, NOT text: {findings_items}
  
  ACTIONS (right/bottom) - Show with ICONS:
    - Use checkmark or tool icons
    - Represent each action with a simple icon, NOT text: {actions_items}
  
  {metaphor_line}
  Emphasis: {emphasis}
  Maximum 1-2 word labels per icon
""",
    "recommendations": """
{heading} Section (Recommendations - Visual Callout):
  ⚠️ USE CHECKMARK ICONS NOT BULLET TEXT
  
  Style: Highlighted box with ICONS
  - Use large checkmark or lightbulb icons
  - Each recommendation shown as an ICON with 1-2 word label max:
{items_formatted}
  
  {metaphor_line}
  Emphasis: {emphasis} - {emphasis_instruction}
  DO NOT write full sentences - use icons with tiny labels only
""",
    "outcome": """
{heading} Section (Outcome - Visual Summary):
  ⚠️ USE SUCCESS ICONS AND IMAGERY
  
  Style: Trophy, star, or success imagery
  - Show outcomes through visual symbols, NOT text paragraphs
  - Each point as an icon with 1-word label:
{points_formatted}
  
  {metaphor_line}
  Emphasis: {emphasis}
""",
    "metric": """
{heading} Section (Metrics - Visual Data):
  ⚠️ USE CHARTS, GAUGES, OR LARGE NUMBERS
  
  Style: Data visualization with minimal text
  - Use pie charts, bar charts, or gauge icons
  - Numbers displayed large with single-word labels
  - Points to visualize:
{points_formatted}
  
  {metaphor_line}
  Emphasis: {emphasis}
"""
}

EMPHASIS_INSTRUCTIONS = {
    "low": "Small size, subtle positioning, supporting role",
    "medium": "Standard size, balanced positioning, equal visual weight",
    "high": "Large size, prominent positioning, visual focal point with label overlay"
}


def compile_prompt(blueprint: Dict[str, Any]) -> str:
    """
    Compile a Visual Blueprint JSON into a Nano Banana Pro prompt string.
    This is a DETERMINISTIC, rule-based transformation.
    
    Args:
        blueprint: Validated Visual Blueprint JSON object
    
    Returns:
        Complete prompt string for Nano Banana Pro image generation
    """
    
    # Extract top-level fields
    title = blueprint.get("title", "Untitled")
    subtitle = blueprint.get("subtitle", "")
    summary = blueprint.get("summary", "")
    tone = blueprint.get("tone", "professional")
    creativity = blueprint.get("creativity", "subtle")
    layout = blueprint.get("layout", "before_after_with_recommendations")
    palette = blueprint.get("palette", "teal")
    sections = blueprint.get("sections", [])
    
    # Get palette details
    palette_info = PALETTE_DEFINITIONS.get(palette, PALETTE_DEFINITIONS["teal"])
    if palette == "custom" and blueprint.get("custom_colors"):
        palette_desc = f"Custom palette: {', '.join(blueprint['custom_colors'])}"
    else:
        palette_desc = palette_info["description"]
    
    # Get creativity modifiers
    creativity_mod = CREATIVITY_MODIFIERS.get(creativity, CREATIVITY_MODIFIERS["subtle"])
    
    # Get layout instructions
    layout_inst = LAYOUT_INSTRUCTIONS.get(layout, LAYOUT_INSTRUCTIONS["before_after_with_recommendations"])
    
    # Build sections content
    sections_text = _compile_sections(sections, creativity)
    
    # Assemble the full prompt
    prompt = f"""Create a professional, executive-grade infographic image.

=== CRITICAL TEXT RENDERING RULES ===
⚠️ MINIMIZE ALL TEXT IN THE IMAGE - This is the most important rule!
- Use ICONS, SYMBOLS, and ILLUSTRATIONS instead of text wherever possible
- Maximum 3-5 words per label or heading
- NO paragraphs or sentences in the image
- NO bullet point text lists - use visual icons with single-word labels
- Title and subtitle should be the ONLY full text elements
- Replace text descriptions with visual metaphors and illustrations
- If you must include text, keep it to SHORT labels only (1-3 words max)

=== HEADER ===
Title: "{title}"
Subtitle: "{subtitle}"
(These are the ONLY longer text elements allowed)

=== STYLE & TONE ===
- Tone: {tone.capitalize()} consulting/business infographic
- Creativity Level: {creativity.upper()} - {creativity_mod['style']}
- Metaphor Guidelines: {creativity_mod['metaphors']}
- Restrictions: {creativity_mod['restrictions']}

=== COLOR PALETTE ===
- Palette: {palette_desc}
- Primary Color: {palette_info['primary']}
- Secondary Color: {palette_info['secondary']}
- Accent Color: {palette_info['accent']}
- Background: {palette_info['background']}
- Dark/Text Color: {palette_info['dark']}

=== TYPOGRAPHY ===
- Font Style: Clean, modern sans-serif
- Title: Bold, large, prominent at top
- ALL OTHER TEXT: Keep extremely minimal - use icons instead
- NO body text paragraphs
- NO decorative or script fonts

=== LAYOUT ===
{layout_inst}

=== VISUAL CONTENT APPROACH ===
For each section below, create VISUAL REPRESENTATIONS not text:
- Use illustrations, icons, and symbols to convey meaning
- Show concepts through imagery (e.g., tangled wires vs organized rack)
- Use color coding and visual hierarchy
- Add simple 1-2 word labels ONLY where absolutely necessary

{sections_text}

=== TECHNICAL REQUIREMENTS ===
- Output: Single high-resolution PNG image
- Dimensions: 3000x2000 pixels (landscape)
- Background: Clean, solid from palette
- Margins: Adequate whitespace

=== DO's ===
- Use ICONS and ILLUSTRATIONS as primary communication
- Use visual metaphors (before/after imagery)
- Use color to differentiate sections
- Keep any text to 1-3 word labels maximum
- Create clear visual flow without relying on text

=== DON'Ts - CRITICAL ===
- ❌ NO paragraphs or sentences
- ❌ NO bullet point lists with text
- ❌ NO text longer than 3 words (except title/subtitle)
- ❌ NO raw text dumps or walls of text
- ❌ NO spelling out full descriptions - use visuals instead
- ❌ DO NOT include any watermarks or signatures
"""
    
    return prompt.strip()


def _compile_sections(sections: List[Dict[str, Any]], creativity: str) -> str:
    """
    Compile the sections list into formatted prompt text.
    """
    result_parts = []
    
    for i, section in enumerate(sections, 1):
        section_type = section.get("type", "outcome")
        heading = section.get("heading", f"Section {i}")
        emphasis = section.get("emphasis", "medium")
        emphasis_inst = EMPHASIS_INSTRUCTIONS.get(emphasis, EMPHASIS_INSTRUCTIONS["medium"])
        
        # Get metaphor info
        visual_metaphor = section.get("visual_metaphor", "")
        metaphor_direction = section.get("metaphor_direction", "left_vs_right")
        
        if section_type == "before_after":
            before_items = section.get("before", [])
            after_items = section.get("after", [])
            
            # Create metaphor descriptions
            if visual_metaphor and creativity != "none":
                metaphor_parts = visual_metaphor.split(" vs ")
                metaphor_before = f"- Visual Metaphor: {metaphor_parts[0] if metaphor_parts else visual_metaphor}"
                metaphor_after = f"- Visual Metaphor: {metaphor_parts[1] if len(metaphor_parts) > 1 else 'organized, resolved state'}"
            else:
                metaphor_before = ""
                metaphor_after = ""
            
            section_text = SECTION_TEMPLATES["before_after"].format(
                heading=heading,
                before_visual="Chaotic, problematic state illustration",
                before_items="\n    - ".join([""] + before_items) if before_items else "Problem indicators",
                after_visual="Organized, resolved state illustration",
                after_items="\n    - ".join([""] + after_items) if after_items else "Solution indicators",
                metaphor_before=metaphor_before,
                metaphor_after=metaphor_after,
                emphasis=f"{emphasis.upper()} - {emphasis_inst}"
            )
            
        elif section_type == "findings_actions":
            findings_items = section.get("findings", [])
            actions_items = section.get("actions", [])
            metaphor_line = f"Visual Metaphor: {visual_metaphor}" if visual_metaphor and creativity != "none" else ""
            
            section_text = SECTION_TEMPLATES["findings_actions"].format(
                heading=heading,
                findings_items="\n    - ".join([""] + findings_items) if findings_items else "Key findings",
                actions_items="\n    - ".join([""] + actions_items) if actions_items else "Actions taken",
                metaphor_line=metaphor_line,
                emphasis=f"{emphasis.upper()} - {emphasis_inst}"
            )
            
        elif section_type == "recommendations":
            items = section.get("items", [])
            items_formatted = "\n".join([f"    • {item}" for item in items]) if items else "    • Key recommendations"
            metaphor_line = f"Visual Metaphor: {visual_metaphor}" if visual_metaphor and creativity != "none" else ""
            
            section_text = SECTION_TEMPLATES["recommendations"].format(
                heading=heading,
                items_formatted=items_formatted,
                metaphor_line=metaphor_line,
                emphasis=emphasis.upper(),
                emphasis_instruction=emphasis_inst
            )
            
        elif section_type == "outcome":
            points = section.get("points", [])
            points_formatted = "\n".join([f"    • {point}" for point in points]) if points else "    • Key outcomes"
            metaphor_line = f"Visual Metaphor: {visual_metaphor}" if visual_metaphor and creativity != "none" else ""
            
            section_text = SECTION_TEMPLATES["outcome"].format(
                heading=heading,
                points_formatted=points_formatted,
                metaphor_line=metaphor_line,
                emphasis=f"{emphasis.upper()} - {emphasis_inst}"
            )
            
        elif section_type == "metric":
            points = section.get("points", [])
            points_formatted = "\n".join([f"    • {point}" for point in points]) if points else "    • Key metrics"
            metaphor_line = f"Visual Metaphor: {visual_metaphor}" if visual_metaphor and creativity != "none" else ""
            
            section_text = SECTION_TEMPLATES["metric"].format(
                heading=heading,
                points_formatted=points_formatted,
                metaphor_line=metaphor_line,
                emphasis=f"{emphasis.upper()} - {emphasis_inst}"
            )
        else:
            section_text = f"\nSection {i}: {heading}\n  Type: {section_type}\n  Emphasis: {emphasis}\n"
        
        result_parts.append(f"--- SECTION {i} ---\n{section_text}")
    
    return "\n".join(result_parts)


def validate_blueprint(blueprint: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate a blueprint against required schema.
    Returns (is_valid, error_message)
    """
    required_fields = ["title", "sections"]
    
    for field in required_fields:
        if field not in blueprint:
            return False, f"Missing required field: {field}"
    
    if not isinstance(blueprint.get("sections"), list):
        return False, "'sections' must be an array"
    
    if len(blueprint["sections"]) == 0:
        return False, "'sections' must have at least one section"
    
    valid_types = ["before_after", "findings_actions", "recommendations", "outcome", "metric"]
    valid_layouts = ["before_after_with_recommendations", "split_two_column", "process_flow", "summary_grid"]
    valid_creativity = ["none", "subtle", "moderate", "high"]
    valid_palette = ["teal", "warm", "mono", "custom"]
    valid_tone = ["professional", "executive", "technical"]
    valid_emphasis = ["low", "medium", "high"]
    
    # Validate layout
    if blueprint.get("layout") and blueprint["layout"] not in valid_layouts:
        return False, f"Invalid layout: {blueprint['layout']}. Must be one of {valid_layouts}"
    
    # Validate creativity
    if blueprint.get("creativity") and blueprint["creativity"] not in valid_creativity:
        return False, f"Invalid creativity: {blueprint['creativity']}. Must be one of {valid_creativity}"
    
    # Validate palette
    if blueprint.get("palette") and blueprint["palette"] not in valid_palette:
        return False, f"Invalid palette: {blueprint['palette']}. Must be one of {valid_palette}"
    
    # Validate tone
    if blueprint.get("tone") and blueprint["tone"] not in valid_tone:
        return False, f"Invalid tone: {blueprint['tone']}. Must be one of {valid_tone}"
    
    # Validate sections
    for i, section in enumerate(blueprint["sections"]):
        if "type" not in section:
            return False, f"Section {i+1} missing 'type' field"
        if section["type"] not in valid_types:
            return False, f"Section {i+1} has invalid type: {section['type']}. Must be one of {valid_types}"
        if "heading" not in section:
            return False, f"Section {i+1} missing 'heading' field"
        if section.get("emphasis") and section["emphasis"] not in valid_emphasis:
            return False, f"Section {i+1} has invalid emphasis: {section['emphasis']}. Must be one of {valid_emphasis}"
    
    return True, ""


# Test function
if __name__ == "__main__":
    # Sample blueprint for testing
    sample_blueprint = {
        "title": "Network & CCTV System Overhaul",
        "subtitle": "From Chaos to Control — Saifee Villa, Matheran",
        "summary": "On-site audit found major rack and CCTV risks; corrective actions implemented and recommendations proposed.",
        "tone": "professional",
        "creativity": "moderate",
        "layout": "before_after_with_recommendations",
        "palette": "teal",
        "sections": [
            {
                "id": "rack",
                "type": "before_after",
                "heading": "Network Rack & Power Management",
                "before": ["Unorganized rack with tangled cables", "Mixed PoE and non-PoE devices", "Loose cable crimps"],
                "after": ["Reorganized structured rack", "All devices on UPS", "Proper cable management"],
                "visual_metaphor": "tangled cables like a knot vs neat organized library shelf",
                "metaphor_direction": "left_vs_right",
                "emphasis": "high"
            },
            {
                "id": "cctv",
                "type": "findings_actions",
                "heading": "CCTV System Stabilization",
                "findings": ["Water ingress in cables", "Rust on cameras", "Non-waterproof enclosures"],
                "actions": ["Re-crimped connections", "Cleaned devices", "Validated configurations"],
                "visual_metaphor": "damaged rusty camera vs clean outdoor-rated camera",
                "metaphor_direction": "left_vs_right",
                "emphasis": "medium"
            },
            {
                "id": "recommendations",
                "type": "recommendations",
                "heading": "Key Recommendations",
                "items": [
                    "Install dedicated 8-port PoE switch",
                    "Upgrade to outdoor-rated PoE cameras",
                    "Use waterproof junction boxes"
                ],
                "visual_metaphor": "checklist with green checkmarks",
                "emphasis": "high"
            }
        ]
    }
    
    is_valid, error = validate_blueprint(sample_blueprint)
    if is_valid:
        prompt = compile_prompt(sample_blueprint)
        print(prompt)
    else:
        print(f"Validation error: {error}")
