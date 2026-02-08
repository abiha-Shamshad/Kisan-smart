from flask import Blueprint, request
from .controllers import get_profile, update_profile, change_password, delete_account
from flask_jwt_extended import jwt_required

profile_api = Blueprint('profile_api', __name__)

@profile_api.route('/', methods=['GET'])
@jwt_required()
def get():
    return get_profile()

@profile_api.route('/', methods=['PUT'])
@jwt_required()
def update():
    return update_profile()

@profile_api.route('/password', methods=['PUT'])
@jwt_required()
def password():
    return change_password()

@profile_api.route('/', methods=['DELETE'])
@jwt_required()
def delete():
    return delete_account()
