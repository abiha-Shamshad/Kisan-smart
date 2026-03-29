import os
import base64
import anthropic
from flask import current_app

# --- Prompts & Data ---
PLANT_DIAGNOSTIC_PROMPT = """
Analyze this image of a plant leaf/crop. Identify signs of:
1. Nutrient Deficiencies (Nitrogen, Phosphorus, Potassium, Magnesium, Sulfur).
2. Common Pests or Diseases.
3. Soil Health indicators (e.g. salinity burn, water stress).

Return your analysis in JSON format:
{
  "deficiency": "Short Name (e.g. Nitrogen Deficiency)",
  "description": "Scientific explanation of symptoms seen in the photo.",
  "solution": "Actionable advice for a farmer (fertilizer types, dosage, timing).",
  "confidence": 0.0 to 1.0,
  "crop_detected": "Crop Name",
  "is_mock": false
}
Note: If the image is not a plant, return "deficiency": "Unknown/Invalid Image".
"""

def analyze_plant_with_claude(image_b64, crop_type="wheat"):
    """
    Calls Anthropic's Claude 3.5 Sonnet to analyze a plant tissue sample.
    Fulfills Feature 1: Photo-Based Deficiency Detection.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        # Fallback to simulation if no key is provided
        from .vision_service import analyze_plant_image
        print("WARNING: No ANTHROPIC_API_KEY found. Falling back to simulation.")
        return analyze_plant_image(image_b64, crop_type)

    try:
        # Anthropic requires the data without the prefix: data:image/jpeg;base64,
        if "," in image_b64:
            media_type = image_b64.split(";")[0].split(":")[1]
            image_data = image_b64.split(",")[1]
        else:
            media_type = "image/jpeg"
            image_data = image_b64

        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"Context: This is a {crop_type} crop. {PLANT_DIAGNOSTIC_PROMPT}"
                        },
                    ],
                }
            ],
        )
        
        # Parse text response to extraction JSON 
        raw_text = response.content[0].text
        # In production, use a more robust regex/json parser
        import json
        import re
        
        try:
            # Look for JSON block if Claude adds preamble
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(raw_text)
        except:
            return {
                "deficiency": "Analysis Complete",
                "description": raw_text,
                "solution": "Consult a local agronomist for detailed dosage.",
                "confidence": 0.85,
                "crop_detected": crop_type,
                "is_mock": False
            }

    except Exception as e:
        print(f"Claude API Error: {str(e)}")
        # Fallback if API fails
        from .vision_service import analyze_plant_image
        return analyze_plant_image(image_b64, crop_type)
