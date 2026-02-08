from marshmallow import Schema, fields, validate


class PredictionRequestSchema(Schema):
    nitrogen = fields.Float(required=True, validate=validate.Range(min=0, max=200))
    phosphorus = fields.Float(required=True, validate=validate.Range(min=0, max=200))
    potassium = fields.Float(required=True, validate=validate.Range(min=0, max=200))
    ph = fields.Float(required=True, validate=validate.Range(min=3.0, max=10.0))
    moisture = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    temperature = fields.Float(required=True, validate=validate.Range(min=-10, max=60))
    crop_type = fields.Str(required=True)
    growth_stage = fields.Str(
        required=True,
        validate=validate.OneOf(["Initial", "Vegetative", "Flowering", "Maturity"]),
    )
    farm_area = fields.Float(
        required=True, validate=validate.Range(min=0.1, max=1000.0)
    )


class PredictionResponseSchema(Schema):
    fertilizer_type = fields.Str()
    fertilizer_type_confidence = fields.Float()
    quantity = fields.Float()
    quantity_unit = fields.Str()
    quantity_confidence = fields.Float()
    overall_confidence = fields.Float()
    confidence_level = fields.Str()
    inference_time_ms = fields.Float()
    model_version = fields.Str()
    explanation = fields.Str()
