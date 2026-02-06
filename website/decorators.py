from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role.role_name not in roles:
                flash("You do not have permission to access this page.", category='error')
                return redirect(url_for('views.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required(['Admin'])(f)

def farmer_required(f):
    return role_required(['Farmer'])(f)
