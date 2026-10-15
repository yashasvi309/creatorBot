import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

# =====================================================================
# 1. ARCHITECTURE & ENVIRONMENT SETUP
# =====================================================================
# Load environment variables from the .env file
load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL_NAME = os.getenv("OPENROUTER_MODEL", "google/gemma-3-27b-it").strip()

# Optional OpenRouter identification headers
APP_SITE_URL = os.getenv("APP_SITE_URL", "http://localhost:3000").strip()
APP_TITLE = os.getenv("APP_TITLE", "Open-Source Creator Studio").strip()

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


# =====================================================================
# CORE OPENROUTER CLIENT & UTILITIES
# =====================================================================
def validate_environment() -> bool:
    """
    Verifies that the OpenRouter API key is properly configured in the environment.
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "sk-or-v1-your-api-key-here":
        return False
    return True


def query_openrouter(
    system_instruction: str,
    user_prompt: str,
    temperature: float = 0.7,
    force_json: bool = False
) -> Optional[str]:
    """
    Sends a structured chat completion request to OpenRouter.

    Args:
        system_instruction (str): System persona and behavioral constraints.
        user_prompt (str): The task-specific input data.
        temperature (float): Sampling temperature for creativity vs. determinism.
        force_json (bool): Whether to request JSON object output format.

    Returns:
        Optional[str]: The raw text response from the model, or None if the request fails.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": APP_SITE_URL,
        "X-Title": APP_TITLE,
    }

    payload: Dict[str, Any] = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "top_p": 0.95,
    }

    if force_json:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()

        # Extract assistant message content from OpenRouter's OpenAI-compatible schema
        choices = data.get("choices", [])
        if choices and "message" in choices[0]:
            return choices[0]["message"].get("content", "").strip()

        print(f"\n[ERROR] Unexpected API response structure: {data}")
        return None

    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Network connection failed while reaching {OPENROUTER_API_URL}.")
        print("Please check your internet connection and try again.")
        return None
    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code if http_err.response is not None else "Unknown"
        error_body = http_err.response.text if http_err.response is not None else str(http_err)
        print(f"\n[ERROR] OpenRouter HTTP {status_code} Error: {error_body}")
        return None
    except Exception as e:
        print(f"\n[ERROR] Unexpected error querying OpenRouter: {e}")
        return None


def parse_llm_json(raw_output: str) -> Dict[str, Any]:
    """
    Robustly extracts and parses JSON from LLM output, handling Markdown code fences
    or stray text if the model wraps its response.
    """
    cleaned = raw_output.strip()

    # Strip markdown code blocks if present (e.g., ```json ... ```)
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Fallback: locate the first '{' and last '}'
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "error": "Failed to parse valid JSON from model response.",
            "details": str(e),
            "raw_response": raw_output
        }


# =====================================================================
# 2. AGENT IMPLEMENTATIONS
# =====================================================================

def agent_social_media_captions(topic: str, raw_notes: str) -> str:
    """
    Agent 1: Social Media Captions Agent.
    Converts video topic and raw notes into platform-tailored posts for
    Instagram, X (Twitter), and LinkedIn with hooks and hashtags.
    """
    system_prompt = (
        "You are an expert Social Media Strategist and Copywriter. "
        "Your job is to repurpose raw creator notes into high-engagement, "
        "platform-native social media posts.\n\n"
        "Structure your output clearly into three sections:\n"
        "1. INSTAGRAM: Engaging visual hook, value-driven body copy with clean line breaks, "
        "a call-to-action (CTA), and 5-8 relevant hashtags.\n"
        "2. X (TWITTER): A punchy, high-curiosity hook under 280 characters (or a short 2-part thread) "
        "with 1-2 crisp hashtags.\n"
        "3. LINKEDIN: A professional, story-driven or insight-driven post formatted with bullet points, "
        "a conversation-starting question at the end, and 3-5 industry hashtags."
    )

    user_prompt = (
        f"Video/Content Topic: {topic}\n"
        f"Raw Creator Notes: {raw_notes}\n\n"
        "Generate the formatted social media posts now."
    )

    result = query_openrouter(system_prompt, user_prompt, temperature=0.7)
    return result or "Agent 1 failed to generate social media captions."


def agent_visual_thumbnail_strategy(topic: str, image_folder_path: str) -> Dict[str, Any]:
    """
    Agent 2: Visual Selection & Thumbnail Strategy Agent.
    Reads local image filenames, selects the highest-CTR expression/pose,
    and builds a FLUX/SDXL background generation prompt and text overlay strategy.
    """
    folder = Path(image_folder_path)
    image_files: List[str] = []

    if folder.exists() and folder.is_dir():
        image_files = sorted([
            f.name for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ])

    if not image_files:
        print(f"  [!] No valid images found in '{image_folder_path}'. Using fallback list.")
        image_files = ["shocked_expression.png", "pointing_desk.png", "neutral_laptop.png"]

    system_prompt = (
        "You are an elite YouTube Thumbnail Strategist and AI Art Director. "
        "Analyze the video topic and the list of available creator subject photos. "
        "Select the single photo filename that conveys the highest emotional intrigue and "
        "Click-Through Rate (CTR) potential, then design a cohesive thumbnail concept.\n\n"
        "You MUST respond strictly in valid JSON format with the exact following keys:\n"
        "{\n"
        '  "selected_image": "exact filename from the provided list",\n'
        '  "reasoning": "psychological and visual explanation for why this pose maximizes CTR",\n'
        '  "background_diffusion_prompt": "detailed visual prompt optimized for FLUX.1 / SDXL describing lighting, environment, depth of field, and color grading (excluding the foreground person)",\n'
        '  "text_overlay": "short, punchy 2-5 word text overlay that complements (does not repeat) the video title"\n'
        "}\n"
        "Return ONLY the raw JSON object. Do not wrap in markdown or add extra commentary."
    )

    user_prompt = (
        f"Video Topic: {topic}\n"
        f"Available Subject Photos: {json.dumps(image_files)}\n\n"
        "Output the JSON thumbnail strategy:"
    )

    raw_response = query_openrouter(
        system_prompt,
        user_prompt,
        temperature=0.4,
        force_json=True
    )

    if not raw_response:
        return {"error": "Agent 2 failed to get a response from OpenRouter."}

    return parse_llm_json(raw_response)


def agent_youtube_seo_copywriting(topic: str, raw_notes: str) -> str:
    """
    Agent 3: YouTube SEO & Copywriting Agent.
    Produces 3 high-CTR titles, a structured video description with timestamp
    placeholders, and 10 targeted SEO tags.
    """
    system_prompt = (
        "You are a YouTube Growth & SEO Specialist. Given a video topic and raw notes, "
        "produce a complete YouTube publishing package containing:\n\n"
        "1. HIGH-CTR TITLES: Exactly 3 distinct, compelling video titles under 65 characters "
        "(using curiosity gaps, strong value propositions, or Contrarian/How-To framing).\n"
        "2. VIDEO DESCRIPTION: An SEO-optimized opening paragraph (first 2 lines optimized for search), "
        "a brief summary of key takeaways, a 'TIMESTAMPS' section with logical placeholder chapters "
        "(e.g., 00:00 Intro, 01:45 ...), and placeholder links for resources/socials.\n"
        "3. TARGETED TAGS: A comma-separated list of exactly 10 high-intent YouTube SEO tags."
    )

    user_prompt = (
        f"Video Topic: {topic}\n"
        f"Raw Notes: {raw_notes}\n\n"
        "Generate the YouTube SEO & Copywriting package now."
    )

    result = query_openrouter(system_prompt, user_prompt, temperature=0.6)
    return result or "Agent 3 failed to generate YouTube SEO metadata."


# =====================================================================
# 3. CENTRAL PIPELINE ORCHESTRATOR
# =====================================================================
def run_pipeline(topic: str, notes: str, image_dir: str) -> Dict[str, Any]:
    print("=" * 72)
    print("🚀 OPEN-SOURCE CREATOR STUDIO PIPELINE (OPENROUTER EDITION)")
    print("=" * 72)

    if not validate_environment():
        sys.exit(1)

    pipeline_results: Dict[str, Any] = {}

    # --- Step 1: Social Media Captions Agent ---
    print("▶️ [Agent 1/3] Running Social Media Captions Agent...")
    pipeline_results["social_captions"] = agent_social_media_captions(topic, notes)
    
    print("⏳ Pausing for 3 seconds to prevent API rate limits...")
    time.sleep(3) # <-- ADD DELAY HERE

    # --- Step 2: Visual Selection & Thumbnail Strategy Agent ---
    print("▶️ [Agent 2/3] Running Visual Selection & Thumbnail Strategy Agent...")
    pipeline_results["thumbnail_strategy"] = agent_visual_thumbnail_strategy(topic, image_dir)
    
    print("⏳ Pausing for 3 seconds to prevent API rate limits...")
    time.sleep(3) # <-- ADD DELAY HERE

    # --- Step 3: YouTube SEO & Copywriting Agent ---
    print("▶️ [Agent 3/3] Running YouTube SEO & Copywriting Agent...")
    pipeline_results["youtube_seo"] = agent_youtube_seo_copywriting(topic, notes)

    print("🎉 PIPELINE EXECUTION COMPLETE!")
    return pipeline_results

# =====================================================================
# DUMMY ENVIRONMENT SETUP & ENTRY POINT
# =====================================================================
def setup_dummy_assets(asset_dir: str) -> None:
    """
    Creates a local directory with dummy image files so the script can be
    tested out-of-the-box without requiring pre-existing photos.
    """
    folder = Path(asset_dir)
    folder.mkdir(parents=True, exist_ok=True)

    dummy_filenames = [
        "shocked_hands_on_head_closeup.png",
        "pointing_at_glowing_laptop_screen_excited.jpg",
        "neutral_sitting_at_desk_drinking_coffee.jpg",
        "skeptical_raised_eyebrow_holding_gpu.png",
        "smiling_thumbs_up_studio_lighting.webp"
    ]

    created_count = 0
    for fname in dummy_filenames:
        file_path = folder / fname
        if not file_path.exists():
            file_path.write_bytes(b"DUMMY_IMAGE_PLACEHOLDER")
            created_count += 1

    if created_count > 0:
        print(f"[Setup] Created {created_count} dummy image files in '{folder.resolve()}'.")


if __name__ == "__main__":
    # Define test inputs
    SAMPLE_ASSET_DIR = "./creator_assets"
    SAMPLE_TOPIC = "Building an Autonomous AI Agent System in 24 Hours"
    SAMPLE_NOTES = (
        "- Powered by open-weight models via OpenRouter & Python.\n"
        "- Orchestrated with lightweight Python (no bloated frameworks).\n"
        "- Automates social media captions, FLUX/SDXL thumbnail prompts, and YouTube SEO.\n"
        "- Fractions of a cent per run compared to $100+/month SaaS wrappers.\n"
        "- Instant model hot-swapping via environment variables."
    )

    # Create dummy asset directory & files for immediate testing
    setup_dummy_assets(SAMPLE_ASSET_DIR)

    # Execute the full pipeline
    run_pipeline(
        topic=SAMPLE_TOPIC,
        notes=SAMPLE_NOTES,
        image_dir=SAMPLE_ASSET_DIR
    )
