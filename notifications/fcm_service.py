import requests
from django.conf import settings

class FCMNotificationService:
    FCM_URL = "https://fcm.googleapis.com/fcm/send"

    def __init__(self, server_key):
        self.server_key = server_key

    def send_notification(self, registration_id, title, body, data=None):
        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "to": registration_id,
            "notification": {
                "title": title,
                "body": body,
            },
            "data": data or {},
        }
        response = requests.post(self.FCM_URL, json=payload, headers=headers)
        return response.status_code, response.json()
