import os
from flask import Flask, request, render_template, redirect
import stripe
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

#Configuration
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Initialize Stripe with test secret key
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

from flask import redirect, url_for

# Add this new route to catch base URL traffic
@app.route("/")
def home():
    # Automatically redirects users to the booking page
    return redirect(url_for('book_consult'))

# (Make sure 'book_consult' matches the exact function name of your booking route)

def allowed_file(filename):
    """Validate the file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            # Railway uses 'MYSQLHOST', defaults to 'localhost' locally
            host=os.environ.get("MYSQLHOST", "localhost"),
            
            # Railway generates a random DB name like 'railway', defaults to 'fullstack_db' locally
            database=os.environ.get("MYSQLDATABASE", "fullstack_db"),
            
            # Railway usually uses 'root', but we make it dynamic
            user=os.environ.get("MYSQLUSER", "root"),
            
            # Railway generates a secure password, fallback to local
            password=os.environ.get("MYSQLPASSWORD", "TrU3eMa5sT3Er#70"),
            
            # Railway uses a specific port, default to 3306 locally
            port=int(os.environ.get("MYSQLPORT", 3306))
        )
        return connection, None
    except Exception as e:
        return None, str(e)

# Route to serve page and initialize transaction
@app.route("/book_consult", methods=["GET"])
def render_booking_page():
    # Create a payment for $50 (amount always in cents for stripe)
    intent = stripe.PaymentIntent.create(
        amount=5000,  # $50.00 in cents
        currency='usd',
    )
    # Pass secure token to HTML template
    return render_template('book_consult.html', client_secret=intent.client_secret)

@app.route("/submit_consultation", methods=["POST"])
def submit_consultation():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    consult_date = request.form.get("date")
    consult_time = request.form.get("time")
    booking_message = request.form.get('booking_message')

    stripe_payment_id = request.form.get("stripe_payment_id")
    payment_status = "Completed" if stripe_payment_id else "Failed"

    # File upload handling
    file_path = None
    if 'project_file' in request.files:
        file = request.files['project_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            file_path = save_path

    # MODIFIED: Extract the connection and the raw error
    conn, db_error = get_db_connection()
    
    if db_error:
        # Renders the exact MySQL exception in your browser
        return f"CRITICAL DATABASE ERROR: {db_error}", 500
        
    if not conn or not conn.is_connected():
        return "Connection failed silently without throwing an exception.", 500

    try:
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO consultations
            (first_name, last_name, email, phone, consult_date, consult_time, booking_message, file_path, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        record_tuple = (first_name, last_name, email, phone, consult_date, consult_time, booking_message, file_path, stripe_payment_id)

        # 1. Execute the save
        cursor.execute(insert_query, record_tuple)
        conn.commit()

        # 2. Get the ID of the row that was just created
        new_booking_id = cursor.lastrowid

        # 3. Query the database to retrieve the verified data
        cursor.execute("SELECT first_name, consult_date, consult_time FROM consultations WHERE consultation_id = %s", (new_booking_id,))
        saved_record = cursor.fetchone()

        # 4. Extract the values from the returned tuple
        db_first_name = saved_record[0]
        db_date = saved_record[1]
        db_time = saved_record[2]

        # 5. Render the HTML page, injecting the database variables
        return render_template("success.html", first_name=db_first_name, date=db_date, time=db_time)

    except Error as e:
        print(f"Failed to process record: {e}")
        conn.rollback()
        return "An error occurred while saving your booking.", 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
        
