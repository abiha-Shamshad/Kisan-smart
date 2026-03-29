import random

DEFICIENCIES = {
    "n": {
        "name": "Nitrogen Deficiency",
        "description": "Yellowing of older leaves, starting from the tip in a V-shape. Restricted growth and thin stems.",
        "solution": "Apply Urea (1 bag per acre) before next irrigation.",
        "confidence": 0.92
    },
    "p": {
        "name": "Phosphorus Deficiency",
        "description": "Dark green leaves with purple or reddish tints. Stunted root growth and delayed maturity.",
        "solution": "Apply DAP (1 bag per acre) at root zone.",
        "confidence": 0.88
    },
    "k": {
        "name": "Potassium Deficiency",
        "description": "Burning or browning of leaf margins (edges). Weak stalks and susceptibility to diseases.",
        "solution": "Apply SOP (Soluble Potash) or MOP.",
        "confidence": 0.85
    },
    "mg": {
        "name": "Magnesium Deficiency",
        "description": "Interveinal chlorosis (yellowing between veins) in older leaves. Veins remain green.",
        "solution": "Apply Magnesium Sulfate (Epsom salt) 5kg/acre.",
        "confidence": 0.82
    }
}

def analyze_plant_image(image_data, crop_type="wheat"):
    """
    Simulation of AI Vision Scan.
    In production, this would send image_data to a model like OpenAI gpt-4-vision or a custom CNN.
    """
    
    # Simulate processing time in the caller (already handled by sleep or async)
    
    # Pick a deficiency based on crop patterns
    options = ["n", "p", "k"]
    if crop_type == "maize": options.append("mg")
    
    choice = random.choice(options)
    result = DEFICIENCIES[choice]
    
    return {
        "deficiency": result["name"],
        "description": result["description"],
        "solution": result["solution"],
        "confidence": result["confidence"],
        "crop_detected": crop_type.capitalize(),
        "is_mock": True # Flag to show it's a simulation
    }
