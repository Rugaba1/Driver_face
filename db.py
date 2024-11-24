from mysql import connector
import contextlib
import pickle
import datetime
import requests


def add_face(license_no, firstname, lastname, gender, category,  image, location, citizen):
    conn=connector.connect(user="root", password="", database="police")
    with contextlib.closing(conn.cursor()) as cursor:
        stmt="INSERT INTO driver (Licence_no, Firstname, Lastname, Gender, Category, Image, aid, Nid) "
        stmt+="VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(stmt,[license_no, firstname, lastname, gender, category, image, location, citizen])
        conn.commit()

def get_all_faces_encodings():
    conn=connector.connect(user="root", password="", database="police")  
    with contextlib.closing(conn.cursor()) as cursor:
        stmt="SELECT id,Nid,image FROM driver"
        cursor.execute(stmt)
        encodings= cursor.fetchall()
        if encodings:
            return [{"encodings":pickle.loads(enc[2]), "id":enc[0], "nid":enc[1]} for enc in encodings]
        return encodings


def add_log(d_id):
    conn=connector.connect(user="root", password="", database="police")
    with contextlib.closing(conn.cursor()) as cursor:
        stmt="INSERT INTO log (id, Time_Done) "
        stmt+="VALUES (%s,%s)"
        cursor.execute(stmt,[d_id,str(datetime.datetime.now())])
        conn.commit()

 
def log_incidence(v_id, location):
    conn = connector.connect(user="root", password="", database="police")
    with contextlib.closing(conn.cursor()) as cursor:
         
        stmt = """
            INSERT INTO incidences (location, vid, date_done) 
            VALUES (ST_GeomFromText('POINT(%s %s)'), %s, %s)
        """
        cursor.execute(stmt, (0, 0, v_id, str(datetime.datetime.now().date())))
        conn.commit()


def check_license_category(driver_id):
    conn=connector.connect(user="root", password="", database="police")
    with contextlib.closing(conn.cursor()) as cursor:
        stmt= "SELECT * FROM vehicle "
        stmt+="WHERE Nid=%s"
        cursor.execute(stmt, [driver_id])
        vehicle_info= cursor.fetchone()
        return vehicle_info
# Function to send SMS using Infobip
def lieve_send_sms():
    API_KEY = '61e31b7b6385de96e1d16624cb2b23bc-c242d7ac-18ae-4d0b-a781-b9249e69c63d'
    SENDER_ID = 'myCargo'
    MESSAGE_TEXT = f'The Driver with not valid ID Detected '

    url = "https://api.infobip.com/sms/2/text/advanced"
    headers = {
        "Authorization": f"App {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {
                "from": SENDER_ID,
                "destinations": [
                    {"to": 250780765548}
                ],
                "text": MESSAGE_TEXT
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("SMS sent successfully!")
    else:
        print(f"Failed to send SMS. Status code: {response.status_code}, Response: {response.text}")