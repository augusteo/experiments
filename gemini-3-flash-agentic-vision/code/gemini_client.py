"""
Gemini 3 Flash API client with code execution toggle.
"""

import os
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment
load_dotenv(Path(__file__).parent.parent / ".env")

# Initialize client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-3-flash-preview"


def load_image(image_path: str) -> types.Part:
    """Load an image file and return as Gemini Part."""
    path = Path(image_path)
    with open(path, "rb") as f:
        image_data = f.read()

    # Determine mime type
    suffix = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "image/jpeg")

    return types.Part.from_bytes(data=image_data, mime_type=mime_type)


def run_vision_query(
    image_path: str,
    prompt: str,
    code_execution: bool = False,
    thinking_level: str = "medium"
) -> dict:
    """
    Run a vision query with optional code execution.

    Args:
        image_path: Path to the image file
        prompt: The question/instruction for the model
        code_execution: Whether to enable code execution tools
        thinking_level: "low", "medium", or "high"

    Returns:
        dict with response text, any code executed, and metadata
    """
    image = load_image(image_path)

    # Configure tools based on code_execution flag
    tools = []
    if code_execution:
        tools = [types.Tool(code_execution=types.ToolCodeExecution())]

    # Build config
    config = types.GenerateContentConfig(
        tools=tools,
        thinking_config=types.ThinkingConfig(thinking_level=thinking_level)
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[image, prompt],
            config=config,
        )

        # Parse response
        result = {
            "success": True,
            "text": "",
            "code_executed": [],
            "code_results": [],
            "images_generated": [],
            "raw_parts": [],
        }

        # Extract parts from response
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    result["text"] += part.text
                if hasattr(part, "executable_code") and part.executable_code:
                    result["code_executed"].append(part.executable_code.code)
                if hasattr(part, "code_execution_result") and part.code_execution_result:
                    result["code_results"].append(part.code_execution_result.output)
                if hasattr(part, "inline_data") and part.inline_data:
                    result["images_generated"].append({
                        "mime_type": part.inline_data.mime_type,
                        "data": base64.b64encode(part.inline_data.data).decode()
                    })
                result["raw_parts"].append(str(part)[:500])  # Truncate for logging

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "code_executed": [],
            "code_results": [],
            "images_generated": [],
        }


def test_connection() -> bool:
    """Test API connection with a simple text query."""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents="Say 'API connection successful' and nothing else.",
        )
        print(f"Connection test: {response.text}")
        return "successful" in response.text.lower()
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Quick test
    if test_connection():
        print("✓ API ready")
    else:
        print("✗ API connection failed - check your GOOGLE_API_KEY in .env")
