from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import yaml
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Load database configuration
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.secret_key = 'terrychin'

# Initialize MySQL
mysql = MySQL(app)

# Index route
@app.route('/')
def Index():
    return render_template('index.html')

# Home route
@app.route("/home")
def home():
    if 'loggedin' not in session:
        return redirect(url_for('Login'))
    return render_template('home.html', name=session['id'])

# Sign-up route
@app.route('/signup', methods=['POST', 'GET'])
def SignUp():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        email = userDetails['email']
        gender = userDetails['gender']
        password = userDetails['password']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(id, email, gender, password) VALUES(%s, %s, %s, %s)", (id, email, gender, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("home"))
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['POST', 'GET'])
def Login():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s AND password=%s', (id, password))
        record = cur.fetchone()
        if record:
            session['loggedin'] = True
            session['id'] = record[0]
            session['name'] = record[1]
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password. Try again!'
            return render_template('index.html', msg=msg)
    
    return render_template('signin.html')

# Room status route
@app.route('/room')
def room_status():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT number FROM rooms WHERE chosen_by = %s", (user_id,))
    chosen_room = cur.fetchone()

    if chosen_room:
        return redirect(url_for('room_confirmation', room_number=chosen_room['number']))
    else:
        return redirect(url_for('room_list'))

# Room list route
@app.route('/room-list')
def room_list():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    return render_template('room_list.html', rooms=rooms)

# Room change request route
@app.route('/room_change_request')
def room_change_request():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT number FROM rooms WHERE chosen_by = %s", (user_id,))
    chosen_room = cur.fetchone()

    cur.close()
    return render_template('room_change.html', room_number=chosen_room['number'] if chosen_room else None)

# Choose room route
@app.route('/choose-room', methods=['POST'])
def choose_room():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    room_number = request.form['room_number']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT chosen_by FROM rooms WHERE number = %s", (room_number,))
    room = cursor.fetchone()

    if room and room['chosen_by'] is None:
        # Check if the user has already chosen a room
        cursor.execute("SELECT number FROM rooms WHERE chosen_by = %s", (user_id,))
        existing_room = cursor.fetchone()

        if existing_room:
            # Update existing room
            cursor.execute("UPDATE rooms SET chosen_by = NULL WHERE number = %s", (existing_room['number'],))

        # Set the new room as chosen by the user
        cursor.execute("UPDATE rooms SET chosen_by = %s WHERE number = %s", (user_id, room_number))
        mysql.connection.commit()
        cursor.close()

        # Set room number in session
        session['room_number'] = room_number

        return redirect(url_for('room_status'))
    elif room:
        cursor.close()
        return redirect(url_for('room_list', error='Room is already chosen'))
    else:
        cursor.close()
        return redirect(url_for('room_list', error='Room not found'))



@app.route('/room_confirmation', methods=['GET', 'POST'])
def room_confirmation():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    room_number = session.get('room_number')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'finalize':
            # Handle finalization
            date_in = session.get('date_in')
            date_out = session.get('date_out')
            cost = session.get('cost')

            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO booking (usersid, roomno, datein, dateout, cost, status) VALUES (%s, %s, %s, %s, %s, %s)",
                           (user_id, room_number, date_in, date_out, cost, 'Confirmed'))
            mysql.connection.commit()
            cursor.close()

            return render_template('booking_success.html', room_number=room_number, date_in=date_in, date_out=date_out, cost=cost)

        elif action == 'feedback':
            feedback_text = request.form.get('feedback')
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO feedback (user_id, feedback) VALUES (%s, %s)", (user_id, feedback_text))
            mysql.connection.commit()
            cursor.close()

            return redirect(url_for('room_status'))

        elif action == 'request_room_change':
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE booking SET status = 'Room Change Requested' WHERE usersid = %s AND roomno = %s", (user_id, room_number))
            mysql.connection.commit()
            cursor.close()

            return redirect(url_for('room_status'))

    # If GET request
    return render_template('room_confirmation.html', room_number=room_number,
                           date_in=session.get('date_in'),
                           date_out=session.get('date_out'),
                           cost=session.get('cost'))



# Confirm room route
@app.route('/confirm_room', methods=['POST'])
def confirm_room():
    user_id = session.get('id')
    room_number = session.get('room_number')

    if not user_id or not room_number:
        return redirect(url_for('Login'))

    date_in = session.get('date_in')
    date_out = session.get('date_out')
    cost = session.get('cost')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("INSERT INTO booking (usersid, roomno, datein, dateout, cost, status) VALUES (%s, %s, %s, %s, %s, %s)",
                   (user_id, room_number, date_in, date_out, cost, 'Pending'))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('confirmation_success'))

# Confirmation success route
@app.route('/confirmation_success')
def confirmation_success():
    return "Your room choice has been confirmed. Awaiting admin approval."

# Admin approval route
@app.route('/admin/approve_room/<int:order_no>', methods=['POST'])
def approve_room(order_no):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("UPDATE booking SET status = 'Approved' WHERE orderno = %s", (order_no,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('admin_dashboard'))

# Admin dashboard route
@app.route('/admin/dashboard')
def admin_dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM booking WHERE status = 'Pending'")
    bookings = cursor.fetchall()
    cursor.close()
    return render_template('admin_dashboard.html', bookings=bookings)

# Feedback route
@app.route('/feedback', methods=['POST'])
def feedback():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    feedback_text = request.form['feedback']
    # Save feedback to the database
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO feedback (user_id, feedback) VALUES (%s, %s)", (user_id, feedback_text))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('room_status'))

# Room change request route
@app.route('/request_room_change', methods=['POST'])
def request_room_change():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    room_number = session.get('room_number')
    # Process room change request
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE booking SET status = 'Room Change Requested' WHERE usersid = %s AND roomno = %s", (user_id, room_number))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('room_status'))

# Cost calculation function
def calculate_cost(date_in, date_out):
    date_format = "%Y-%m-%d"
    d1 = datetime.strptime(date_in, date_format)
    d2 = datetime.strptime(date_out, date_format)
    delta = d2 - d1
    days = delta.days

    cost_per_day = 50
    total_cost = days * cost_per_day
    return total_cost

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
