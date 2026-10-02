import os
from flask import Flask, request, render_template, redirect
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

#Configuration
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Validate the file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Establish connection to MySQL"""
    try:
        connection = mysql.connector.connect(
            host = os.environ.get("MYSQLHOST","localhost"),
            database = os.environ.get("MYSQLDATABASE", "fullstack_db"),
            user = os.environ.get("MYSQLUSER", "root"),
            password = os.environ.get("MYSQLPASSWORD", 'TrU3eMa5sT3Er#70'),
            port = os.environ.get("MYSQLPORT", 3306)
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None 

@app.route("/submit_consultation", methods=["POST"])
def submit_consultation():
    # 1. Extract standard form data
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    consult_date = request.form.get("date")
    consult_time = request.form.get("time")
    booking_message = request.form.get('booking_message')

    #Simulate payment processing step here (e.g., Stripe API call)
    payment_status = "Completed"

    # 2. Handle file upload
    file_path = None
    if 'project_file' in request.files:
        file = request.files['project_file']
        if file and file.name != '' and allowed_file(file.filename):
            # secure_filename prevents directory traversal attacks
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            file_path = save_path

    # 3. Save to database
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO consultations
            (first_name, last_name, email, phone, consult_date, consult_time, booking_message, file_path, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        record_tuple = (first_name, last_name, email, phone, consult_date, consult_time, booking_message, file_path, payment_status)

        try:
            cursor.execute(insert_query, record_tuple)
            conn.commit()
            return "Consultation booked successfully!", 200
        except Error as e:
            print(f"Failed to insert record: {e}")
            conn.rollback()
            return "An error occurred while saving your booking. Please check server logs.", 500
        finally:
            cursor.close()
            conn.close()

    # Redirect to a success page or render a template
    return "Consultation booked successfully!"

if __name__ == '__main__':
    app.run(debug=True)
        
