from pywebpush import webpush, WebPushException

VAPID_PRIVATE_KEY = "EavFauR57UWsxOrgDJhKQvLuinGUYUJ7cGPJS-Hus_o"
VAPID_CLAIMS = {
    "sub": "mailto:krishnaawasthi2005@gmail.com"
}

def send_web_push(subscription_info, message):
    try:
        webpush(
            subscription_info,
            message,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        print("Push notification sent!")
    except WebPushException as ex:
        print("Web push failed:", repr(ex))
