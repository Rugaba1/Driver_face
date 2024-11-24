from flask import Flask, jsonify, render_template
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",        
        user="root",             
        password="",  
        database="police"
    )

@app.route('/')
def index():
    return render_template('index.html')  

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

if __name__ == '__main__':
    app.run(debug=True)
