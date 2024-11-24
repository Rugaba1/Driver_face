from flask import Flask, jsonify, render_template, request
import mysql.connector
import os
import pickle
import cv2
import numpy as np
import face_recognition
from db import add_face 

app = Flask(__name__)

ALLOWED_EXTENSIONS = [".jpg", ".png", ".jpeg"]
FACE_ENCODINGS_FOLDER = "encodings"
FACE_THRESHOLD = 0.3
CAM_IP="http://192.168.56.94:4747"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",        
        user="root",             
        password="",  
        database="police"
    )


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', cam_ip=CAM_IP)


@app.route('/get-addresses', methods=['GET'])
def get_addresses():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT aid, district FROM address")
    addresses = cursor.fetchall()

    cursor.execute("SELECT Firstname, Nid FROM citizen")
    citizens = cursor.fetchall()

    cursor.close()
    conn.close()

    response_data = {
        "addresses": [{"aid": row[0], "district": row[1]} for row in addresses],
        "citizens": [{"Firstname": row[0], "Nid": row[1]} for row in citizens]
    }
    return jsonify(response_data)


@app.route("/add-face", methods=["POST"])
def create():
    data = request.form
    id = data.get("id")
    image = request.files.get("image")
    license_no = data.get("license_no")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    location = data.get("address")
    gender = data.get("gender")
    category = data.get("category")
    citizen = data.get("citizen")

    if not all([image, license_no, first_name, last_name, location, gender, category,citizen]):
        return jsonify({"error": "Missing required fields"}), 400

    _, ext = os.path.splitext(image.filename)
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"message": "The uploaded file is not supported"}), 400

    try:
        with open(f"{FACE_ENCODINGS_FOLDER}/known_encodings.dat", "rb") as f:
            try:
                known_encodings = pickle.load(f)
            except EOFError:
                known_encodings = []

            image_bytes = image.read()
            np_arr = np.frombuffer(image_bytes, np.uint8)
            cv2_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            cvt_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

            faces_in_img = face_recognition.face_locations(cvt_img)
            if len(faces_in_img) <= 0 or len(faces_in_img) > 1:
                return jsonify({"message": "The uploaded image contains zero or many faces"}), 400

            face_encodings = face_recognition.face_encodings(cvt_img)
            known_encodings.append({"id": id, "encodings": face_encodings})

           
            encoding = pickle.dumps(face_encodings[0])
            add_face(license_no, first_name, last_name, gender, category, encoding, location, citizen)

            return jsonify({"message": "Face uploaded successfully"}), 200

    except FileNotFoundError:
        return jsonify({"message": "Unable to locate known_encodings.dat file"}), 500

@app.route("/verify-face", methods=["POST", "GET"])
def verify_face():
    data = request.form
    id = data.get("id")
    image = request.files.get("image")

    if not all([id, image]):
        return jsonify({"error": "Missing required fields"}), 400

    _, ext = os.path.splitext(image.filename)
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"message": f"The uploaded file is not supported {ext}"}), 400

    try:
        with open(f"{FACE_ENCODINGS_FOLDER}/known_encodings.dat", "rb") as f:
            try:
                known_encodings = pickle.load(f)
            except EOFError:
                known_encodings = []

            image_bytes = image.read()
            np_arr = np.frombuffer(image_bytes, np.uint8)
            cv2_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            cvt_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

            faces_in_img = face_recognition.face_locations(cvt_img)
            if len(faces_in_img) <= 0 or len(faces_in_img) > 1:
                return jsonify({"message": "The uploaded image contains zero or many faces"}), 400

            face_encodings = face_recognition.face_encodings(cvt_img)
            if not known_encodings:
                return jsonify({"message": "No face image uploaded yet"}), 204

            known_encodings_list = [enc["encodings"][0] for enc in known_encodings]
            known_ids = [enc["id"] for enc in known_encodings]

            face_dist = face_recognition.face_distance(known_encodings_list, face_encodings[0])
            best_index = np.argmin(face_dist)

            if face_dist[best_index] <= FACE_THRESHOLD:
                return jsonify({"message": "Face found", "id": known_ids[best_index], "dist": face_dist[best_index]}), 200
            else:
                return jsonify({"message": "No match found"}), 404

    except FileNotFoundError:
        return jsonify({"message": "Unable to locate known_encodings.dat file"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
