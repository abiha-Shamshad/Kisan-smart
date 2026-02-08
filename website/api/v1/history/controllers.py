from flask import request
from website.api.v1.utils.responses import success_response, error_response
from website.models import Recommendation, db
from flask_jwt_extended import get_jwt_identity
from website.api.v1.prediction.schemas import PredictionResponseSchema
import pandas as pd
import io
from flask import send_file

prediction_schema = PredictionResponseSchema()

def get_history():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Filtering
    crop_type = request.args.get('crop_type')
    
    query = Recommendation.query.filter_by(user_id=int(user_id))
    
    if crop_type:
        query = query.filter(Recommendation.crop_type.ilike(f"%{crop_type}%"))
        
    pagination = query.order_by(Recommendation.created_at.desc()).paginate(page=page, per_page=per_page)
    
    items = []
    for item in pagination.items:
        items.append({
            "prediction_id": item.prediction_id,
            "crop_type": item.crop_type,
            "fertilizer_type": item.fertilizer_type,
            "quantity": item.quantity,
            "overall_confidence": item.overall_confidence,
            "confidence_level": item.confidence_level,
            "created_at": item.created_at.isoformat()
        })
        
    return success_response({
        "predictions": items,
        "pagination": {
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    }, "History retrieved successfully")

def get_prediction_detail(prediction_id):
    user_id = get_jwt_identity()
    rec = Recommendation.query.filter_by(prediction_id=prediction_id, user_id=int(user_id)).first()
    
    if not rec:
        return error_response("Recommendation not found", "NOT_FOUND", None, 404)
        
    # Manual dump for completeness
    data = {
        "prediction_id": rec.prediction_id,
        "input_summary": {
            "crop_type": rec.crop_type,
            "nitrogen": rec.nitrogen,
            "phosphorus": rec.phosphorus,
            "potassium": rec.potassium,
            "ph": rec.ph,
            "moisture": rec.moisture,
            "temperature": rec.temperature,
            "farm_area": rec.farm_area,
            "growth_stage": rec.growth_stage
        },
        "fertilizer_type": rec.fertilizer_type,
        "quantity": rec.quantity,
        "quantity_unit": rec.quantity_unit,
        "confidence": {
            "type_confidence": rec.type_confidence,
            "quantity_confidence": rec.quantity_confidence,
            "overall_confidence": rec.overall_confidence,
            "level": rec.confidence_level
        },
        "created_at": rec.created_at.isoformat()
    }
    
    return success_response(data, "Detail retrieved")

def delete_prediction(prediction_id):
    user_id = get_jwt_identity()
    rec = Recommendation.query.filter_by(prediction_id=prediction_id, user_id=int(user_id)).first()
    
    if not rec:
        return error_response("Recommendation not found", "NOT_FOUND", None, 404)
        
    db.session.delete(rec)
    db.session.commit()
    return success_response(None, "Record deleted successfully")

def export_history():
    user_id = get_jwt_identity()
    recs = Recommendation.query.filter_by(user_id=int(user_id)).all()
    
    if not recs:
        return error_response("No history to export", "EMPTY_HISTORY", None, 400)
        
    # Convert to DF for easy export
    data = []
    for r in recs:
        data.append({
            "Date": r.created_at,
            "Crop": r.crop_type,
            "N": r.nitrogen, "P": r.phosphorus, "K": r.potassium,
            "pH": r.ph, "Area": r.farm_area,
            "Fertilizer": r.fertilizer_type,
            "Quantity": r.quantity,
            "Confidence": r.overall_confidence
        })
        
    df = pd.DataFrame(data)
    proxy = io.StringIO()
    df.to_csv(proxy, index=False)
    
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode())
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'kisan_smart_history_{datetime.now().strftime("%Y%m%d")}.csv'
    )
