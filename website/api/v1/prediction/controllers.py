from flask import request
from website.api.v1.utils.responses import success_response, error_response
from website.api.v1.prediction.schemas import PredictionRequestSchema
from website.api.v1.prediction.ml_service import ml_service
from website.models import Recommendation, db
from flask_login import current_user
import uuid
from datetime import datetime

predict_schema = PredictionRequestSchema()


from website.api.v1.prediction.tools_service import (
    calculate_npk_formula,
    optimize_budget_logic,
    generate_schedule_logic,
)
from website.api.v1.prediction.vision_service import (
    analyze_plant_image,
)
from website.api.v1.prediction.ai_vision_service import (
    analyze_plant_with_claude,
)


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
        user_id = getattr(current_user, "id", None) if current_user.is_authenticated else None
        prediction_id = f"pred_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"

        if user_id:
            new_rec = Recommendation(
                user_id=int(user_id),
                prediction_id=prediction_id,
                crop_type=data["crop_type"],
                nitrogen=data["nitrogen"],
                phosphorus=data["phosphorus"],
                potassium=data["potassium"],
                ph=data["ph"],
                moisture=data["moisture"],
                temperature=data["temperature"],
                farm_area=data["farm_area"],
                growth_stage=data["growth_stage"],
                fertilizer_type=result["fertilizer_type"],
                quantity=result["quantity"],
                type_confidence=result["confidence"]["fertilizer_type_confidence"],
                quantity_confidence=result["confidence"]["quantity_confidence"],
                overall_confidence=result["confidence"]["overall_confidence"],
                confidence_level=result["confidence"]["level"],
            )
            db.session.add(new_rec)
            db.session.commit()
            result["prediction_id"] = prediction_id

        return success_response(result, "Recommendation generated successfully")

    except Exception as e:
        return error_response(str(e), "PREDICTION_FAILED", None, 500)


def get_batch_prediction():
    data_list = request.get_json()
    if not isinstance(data_list, list):
        return error_response(
            "Input must be a list of objects", "INVALID_INPUT_FORMAT", None, 400
        )

    results = []
    for item in data_list[:50]:  # Limit to 50 for performance
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


def get_npk_formula_prediction():
    """Formula-based NPK Calculator"""
    try:
        data = request.get_json()
        result = calculate_npk_formula(data)
        
        # Save to history if logged in
        if current_user.is_authenticated:
            prediction_id = f"calc_{int(datetime.now().timestamp())}"
            new_rec = Recommendation(
                user_id=int(current_user.id),
                prediction_id=prediction_id,
                crop_type=data.get("crop_type", "Wheat"),
                nitrogen=float(data.get("nitrogen", 0)),
                phosphorus=float(data.get("phosphorus", 0)),
                potassium=float(data.get("potassium", 0)),
                ph=float(data.get("ph", 7)),
                moisture=40, temperature=25, # defaults
                farm_area=float(data.get("field_area", 1)),
                growth_stage="Basal",
                fertilizer_type=f"DAP: {result['fertilizers']['dap']}kg, Urea: {result['fertilizers']['urea']}kg",
                quantity=result['fertilizers']['dap'] + result['fertilizers']['urea'] + result['fertilizers']['sop'],
                type_confidence=100.0,
                quantity_confidence=100.0,
                overall_confidence=100.0,
                confidence_level="Calculated",
            )
            db.session.add(new_rec)
            db.session.commit()

        return success_response(result, "Calculation completed")
    except Exception as e:
        return error_response(str(e), "CALCULATION_FAILED", None, 500)


def get_budget_optimization():
    """Budget Optimizer Controller"""
    try:
        data = request.get_json()
        result = optimize_budget_logic(data)
        return success_response(result, "Optimization successful")
    except Exception as e:
        return error_response(str(e), "OPTIMIZATION_FAILED", None, 500)


def get_schedule():
    """Schedule Generator Controller"""
    try:
        data = request.get_json()
        result = generate_schedule_logic(data)
        return success_response(result, "Schedule generated")
    except Exception as e:
        return error_response(str(e), "SCHEDULE_GENERATION_FAILED", None, 500)


def get_ai_scan():
    """AI Vision Diagnostic Controller"""
    try:
        data = request.get_json()
        img_b64 = data.get("image")
        crop = data.get("crop_type", "wheat")
        
        # Use Claude for advanced diagnostics (Feature 1)
        result = analyze_plant_with_claude(img_b64, crop)
        return success_response(result, "Diagnosis complete")
    except Exception as e:
        return error_response(str(e), "AI_SCAN_FAILED", None, 500)


def validate_input():
    data = request.get_json()
    errors = predict_schema.validate(data)
    if errors:
        return success_response({"valid": False, "errors": errors}, "Validation failed")
    return success_response({"valid": True}, "Input is valid")
