import os
import requests
import threading
from db import log_incidence

phone_number = os.environ.get("PHONE_NUMBER")
sms_url = os.environ.get("INFOBIP_API_URL")
camera_url = os.environ.get("CAMERA_URL")
key = os.environ.get("INFOBIP_API_KEY")
sender = os.environ.get("SENDER_PHONE_NUMBER")
headers = {
    "Authorization": f"App {key}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def __send(message):
    sms_payload = {
        "messages": [
            {
                "destinations": [{"to": phone_number}],
                "from": sender,
                "text": message,
            }
        ]
    }
    try:
        response = requests.post(sms_url, headers=headers, json=sms_payload)
        if response.status_code == 200:
            print(response.content)
    except Exception as e:
        print(str(e))


def send_sms(message):
    sms_thread = threading.Thread(target=__send, args=[message])
    sms_thread.start()


def _send_feedback(feeback):
    try:
        response = requests.post(f"{camera_url}/feedback", data=feeback)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send feedback: {e}")


def send_feedback(feedback):
    feedback_thread = threading.Thread(target=_send_feedback, args=[feedback])
    feedback_thread.start()


def log_incidence(location):
    log_incidence(location)