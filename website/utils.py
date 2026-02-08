from flask import url_for, current_app
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from . import mail

def send_verification_email(user):
    token = generate_token(user.email, salt='email-confirm')
    msg = Message('Verify Your Email - Kisan Smart',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    link = url_for('auth.verify_email', token=token, _external=True)
    msg.body = f'''To verify your account, visit the following link:
{link}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    msg.html = f'''<h3>Verify Your Email - Kisan Smart</h3>
<p>To verify your account, click the link below:</p>
<a href="{link}">{link}</a>
<p>If you did not make this request then simply ignore this email and no changes will be made.</p>
'''
    mail.send(msg)

def send_reset_email(user):
    token = generate_token(user.email, salt='password-reset')
    msg = Message('Password Reset Request - Kisan Smart',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    link = url_for('auth.reset_password', token=token, _external=True)
    msg.body = f'''To reset your password, visit the following link:
{link}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    msg.html = f'''<h3>Password Reset Request - Kisan Smart</h3>
<p>To reset your password, click the link below:</p>
<a href="{link}">{link}</a>
<p>If you did not make this request then simply ignore this email and no changes will be made.</p>
'''
    mail.send(msg)

def generate_token(email, salt):
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt=salt)

def verify_token(token, salt, expiration=3600):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt=salt, max_age=expiration)
    except:
        return None
    return email
