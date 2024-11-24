from dotenv import load_dotenv
load_dotenv()

import cv2
import face_recognition
import numpy as np
import os
from db import get_all_faces_encodings, check_license_category, log_incidence
import datetime
import requests
import json
import http.client

# Setting up the app URLs
host = os.environ.get("CAMERA_URL")
capture_url = f"{host}/capture"
start_url = f"{host}/start"
stop_url = f"{host}/stop"
gps_url = f"{host}/gps"

# Setting program constants
face_threshold = 0.45
current_driver = None
first_check_time = None   
recheck_time = 1
first_detected=False
rechecked = False
plate = "RAF157F"
category = "B"
v_id = 1
location = "None"
last_message_sent=None
resend_message_time=60
first_message_sent=False

def check_category(d_category):
    global category
    return d_category == category

def capture():
    try:
        resp = requests.get(capture_url)
        if resp.status_code == 200:
            with open("frame.jpg", "wb") as f:
                f.write(resp.content)
            return True
        return False
    except Exception as e:
        print(str(e))
        return False

def start_car():
    try:
        resp = requests.get(start_url)
        if resp.status_code == 200:
            return True
        return False
    except Exception as e:
        print(str(e))
        return False

def stop_car():
    try:
        resp = requests.get(stop_url)
        if resp.status_code == 200:
            return True
        return False
    except Exception as e:
        print(str(e))
        return False

def get_gps_coordinate():
    try:
        resp = requests.get(gps_url)
        if resp.status_code == 200:
            return resp.text
        return False
    except Exception as e:
        print(str(e))
        return False

def send_sms(message):
    global last_message_sent, resend_message_time,first_message_sent
    try:
        conn = http.client.HTTPSConnection("e55d8n.api.infobip.com")
        payload = json.dumps({
            "messages": [
                {
                     "destinations": [{"to":"250784577571"},{"to":"250780765548"}],
                    "from": "447491163443",
                    "text": message
                }
            ]
        })
        headers = {
            'Authorization': 'App a9fc38530883b3c0ce5d7f478f24b67c-da69dba7-8b34-4c90-a4e5-b718cea63369',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        now=datetime.datetime.now()
        if not last_message_sent:
            last_message_sent= now
        if ((now-last_message_sent).seconds >=resend_message_time)or first_message_sent==False:
            print("message sent 3")
            conn.request("POST", "/sms/2/text/advanced", payload, headers)
            res = conn.getresponse()
            data = res.read()
            last_message_sent=now
            first_message_sent=True
            return True, data
    except Exception as e:
        print(str(e))
        return False

def first_check_driver_eligibility(driver_info):
    global current_driver, first_check_time, first_detected
    if not first_detected:
        if check_category(driver_info[4]):
            current_driver = driver_info
            first_check_time = datetime.datetime.now()
            first_detected=True
            start_car()
        else:
            stop_car()
        log_incidence(v_id, location)

def second_check_driver_eligibility(driver_info):
    global rechecked, last_message_sent, first_check_time
    if check_category(driver_info[4]):
        if current_driver != driver_info:
            coordinate = get_gps_coordinate()
            message = f"This car ({plate}) driver changed on the way and he/she doesn't have driving licence or it's type doesent match."
            if coordinate:
                message += f" Location: {coordinate}"
            send_sms(message)

        else:
            rechecked = True
    else:
         send_sms(message)
    first_check_time=datetime.datetime.now()
    log_incidence(v_id, location)


while True:
    known_encodings = get_all_faces_encodings()
    success = capture()
    if not success:
        continue 

    img = cv2.imread("frame.jpg")
    img = cv2.resize(img, (400, 400))
    img = cv2.rotate(img, cv2.ROTATE_180)
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    facesCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    if encodeCurFrame:
        if not known_encodings:
            break
        known_encodings_list = [enc["encodings"] for enc in known_encodings]
        known_ids = [enc["nid"] for enc in known_encodings]
        face_dist = face_recognition.face_distance(
            known_encodings_list, encodeCurFrame[0]
        )
        best_index = np.argmin(face_dist)
        y1, x2, y2, x1 = facesCurFrame[0]
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
        best_driver_id = known_ids[best_index]

        # Get current time
        now = datetime.datetime.now()
        # If face matches within threshold
        if face_dist[best_index] <= face_threshold:
            driver_info = check_license_category(best_driver_id)
            
            # If there's no current driver or time for recheck has arrived
            if current_driver is None :
                first_check_driver_eligibility(driver_info)
            elif (now - first_check_time).seconds >= recheck_time * 60:
                print("rechecked")
                second_check_driver_eligibility(driver_info)

            # Display recognized driver on the screen
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2), (x2, y2 + 70), (0, 255, 0), 2)
            cv2.putText(
                img,
                f"DRIVER DETECTED",
                (x1 + 10, y2 + 30),
                cv2.FONT_HERSHEY_COMPLEX,
                1,
                (255, 255, 255),
                1,
            )
        elif not(face_dist[best_index] <= face_threshold):
            now= datetime.datetime.now()
            if first_check_time:
                if (now - first_check_time).seconds >= recheck_time * 60:
                    print("rechecked")
                    print("message sent")
                    message = f"This car ({plate}) driver changed on the way and he/she doesn't have driving licence or it's type doesent match. {str(now)}"
                    send_sms(message)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 1)
        
    else:
         if first_check_time:
            if (now - first_check_time).seconds >= recheck_time * 60:
                message = f"This car ({plate}) driver changed on the way and he/she doesn't have driving licence or it's type doesent match. {str(now)}"
                send_sms(message)
        
        

    # Display camera feed
    cv2.imshow("FACE RECOGNITION CAMERA", img)
    key = cv2.waitKey(1)
    if key == ord("q"):
        break

cv2.destroyAllWindows()
stop_car()