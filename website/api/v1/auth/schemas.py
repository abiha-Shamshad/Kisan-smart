from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    phone_number = fields.Str(validate=validate.Length(min=10, max=15))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class UserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    username = fields.Str()
    email = fields.Email()
    full_name = fields.Str()
    phone_number = fields.Str()
    is_verified = fields.Boolean()
    created_at = fields.DateTime()
