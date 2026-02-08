from flask import Blueprint, jsonify
from website.api.v1.utils.responses import success_response

reference_api = Blueprint('reference_api', __name__)

CROPS = [
    {"id": "wheat", "name": "Wheat", "description": "Cereal grain, staple food segment."},
    {"id": "rice", "name": "Rice", "description": "High water requirement, tropical crop."},
    {"id": "maize", "name": "Maize", "description": "Versatile corn crop."},
    {"id": "cotton", "name": "Cotton", "description": "Fibre crop, requires warm climate."}
]

FERTILIZERS = [
    {"id": "urea", "name": "Urea", "nutrients": "46-0-0"},
    {"id": "dap", "name": "DAP", "nutrients": "18-46-0"},
    {"id": "mop", "name": "MOP", "nutrients": "0-0-60"},
    {"id": "npk_20_20_20", "name": "NPK 20-20-20", "nutrients": "20-20-20"}
]

@reference_api.route('/crops', methods=['GET'])
def list_crops():
    return success_response(CROPS)

@reference_api.route('/fertilizers', methods=['GET'])
def list_fertilizers():
    return success_response(FERTILIZERS)
