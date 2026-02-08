from flask import request
from website.api.v1.utils.responses import success_response, error_response
from website.api.v1.prediction.schemas import PredictionRequestSchema
from website.api.v1.prediction.ml_service import ml_service
from website.models import Recommendation, db
from flask_jwt_extended import get_jwt_identity
import uuid
from datetime import datetime

predict_schema = PredictionRequestSchema()

def get_prediction():
    """
    Get Fertilizer Recommendation
    ---
    tags:
      - Prediction
    parameters:
      - in: body
        name: body
        schema:
          id: PredictionRequest
          required:
            - nitrogen
            - phosphorus
            - potassium
            - ph
            - moisture
            - temperature
            - crop_type
            - growth_stage
            - farm_area
          properties:
            nitrogen: {type: number, example: 45}
            phosphorus: {type: number, example: 30}
            potassium: {type: number, example: 25}
            ph: {type: number, example: 6.5}
            moisture: {type: number, example: 40}
            temperature: {type: number, example: 25}
            crop_type: {type: string, example: "Wheat"}
            growth_stage: {type: string, example: "Vegetative"}
            farm_area: {type: number, example: 1.5}
    responses:
      200:
        description: Success
      422:
        description: Validation Error
    """
    data = request.get_json()
    errors = predict_schema.validate(data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", errors, 422)
    
    try:
        # Get result from ML Service
        result = ml_service.predict(data)
        
        # Save to history if user is logged in
        user_id = get_jwt_identity()
        prediction_id = f"pred_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
        
        if user_id:
            new_rec = Recommendation(
                user_id=int(user_id),
                prediction_id=prediction_id,
                crop_type=data['crop_type'],
                nitrogen=data['nitrogen'],
                phosphorus=data['phosphorus'],
                potassium=data['potassium'],
                ph=data['ph'],
                moisture=data['moisture'],
                temperature=data['temperature'],
                farm_area=data['farm_area'],
                growth_stage=data['growth_stage'],
                fertilizer_type=result['fertilizer_type'],
                quantity=result['quantity'],
                type_confidence=result['fertilizer_type_confidence'],
                quantity_confidence=result['quantity_confidence'],
                overall_confidence=result['overall_confidence'],
                confidence_level=result['confidence_level']
            )
            db.session.add(new_rec)
            db.session.commit()
            result['prediction_id'] = prediction_id
        
        return success_response(result, "Recommendation generated successfully")
        
    except Exception as e:
        return error_response(str(e), "PREDICTION_FAILED", None, 500)

def get_batch_prediction():
    data_list = request.get_json()
    if not isinstance(data_list, list):
        return error_response("Input must be a list of objects", "INVALID_INPUT_FORMAT", None, 400)
    
    results = []
    for item in data_list[:50]: # Limit to 50 for performance
        errors = predict_schema.validate(item)
        if errors:
            results.append({"error": errors, "success": False})
            continue
        
        try:
            res = ml_service.predict(item)
            results.append({"data": res, "success": True})
        except Exception as e:
            results.append({"error": str(e), "success": False})
            
    return success_response(results, f"Processed {len(results)} predictions")

def validate_input():
    data = request.get_json()
    errors = predict_schema.validate(data)
    if errors:
        return success_response({"valid": False, "errors": errors}, "Validation failed")
    return success_response({"valid": True}, "Input is valid")
