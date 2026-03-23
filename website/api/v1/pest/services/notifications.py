"""
website/api/v1/pest/services/notifications.py
============================================
Push notification (Firebase FCM) + WhatsApp (Twilio) delivery service.
"""

import os
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


# ── Firebase FCM ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_firebase_app():
    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        if not cred_path:
            logger.warning("FIREBASE_CREDENTIALS_PATH not set in environment")
            return None

        cred = credentials.Certificate(cred_path)
        return firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        return None


def send_push_notification(
    token: str,
    title: str,
    body:  str,
    data:  dict = None,
) -> bool:
    try:
        from firebase_admin import messaging
        app = _get_firebase_app()
        if not app: return False

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    icon="ic_kisan_alert",
                    color="#2D6A4F",
                    sound="default",
                ),
            ),
        )
        response = messaging.send(message)
        logger.info(f"FCM sent successfully: {response}")
        return True

    except Exception as e:
        logger.error(f"FCM push failed: {e}")
        return False


def send_bulk_push_notifications(tokens: list[str], title: str, body: str, data: dict = None) -> dict:
    if not tokens:
        return {"success": 0, "failure": 0}

    try:
        from firebase_admin import messaging
        app = _get_firebase_app()
        if not app: return {"success": 0, "failure": len(tokens)}

        total_success = total_failure = 0
        for i in range(0, len(tokens), 500):
            batch = tokens[i:i+500]
            multicast = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                tokens=batch,
            )
            result = messaging.send_each_for_multicast(multicast)
            total_success += result.success_count
            total_failure += result.failure_count

        logger.info(f"Bulk FCM: {total_success} sent, {total_failure} failed")
        return {"success": total_success, "failure": total_failure}

    except Exception as e:
        logger.error(f"Bulk FCM failed: {e}")
        return {"success": 0, "failure": len(tokens)}


# ── WhatsApp via Twilio ────────────────────────────────────────────────────────

def send_whatsapp_alert(phone: str, message: str) -> bool:
    try:
        from twilio.rest import Client

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

        if not account_sid or not auth_token:
            logger.warning("Twilio credentials not configured")
            return False

        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body = message,
            from_= from_number,
            to   = f"whatsapp:{phone}",
        )
        logger.info(f"WhatsApp sent to {phone}: SID={msg.sid}")
        return True

    except Exception as e:
        logger.error(f"WhatsApp send failed to {phone}: {e}")
        return False


def send_sms_alert(phone: str, message: str) -> bool:
    try:
        from twilio.rest import Client

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_SMS_FROM")

        if not all([account_sid, auth_token, from_number]):
            logger.warning("Twilio SMS not configured")
            return False

        client = Client(account_sid, auth_token)
        msg = client.messages.create(body=message, from_=from_number, to=phone)
        logger.info(f"SMS sent to {phone}: SID={msg.sid}")
        return True

    except Exception as e:
        logger.error(f"SMS failed to {phone}: {e}")
        return False
