import os
import requests
import threading

def _send_feedback(feeback):
    try:
        response = requests.post("192.168.59.48/feedback", data=feeback)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send feedback: {e}")

def send_feedback(feedback):
    feedback_thread = threading.Thread(target=_send_feedback, args=[feedback])
    feedback_thread.start()
