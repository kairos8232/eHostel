from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import yaml

main = Flask(__name__)

def create_main():
    main =  Flask(__name__)
    main.config['SECRET_KEY'] = 'Hostel management secret key'
    return main

db = yaml.safe_load(open('db.yaml'))
main.config['MYSQL_HOST'] = db['mysql_host']
main.config['MYSQL_USER'] = db['mysql_user']
main.config['MYSQL_PASSWORD'] = db['mysql_password']
main.config['MYSQL_DB'] = db['mysql_db']
main.secret_key = 'terrychin'

mysql = MySQL(main)


@main.route('/')
def Index():
    return render_template('index.html')

@main.route("/home")
def home():
    print("Session data:", session) #DEBUG USE
    if 'loggedin' not in session:
        return redirect(url_for('Login'))
    return render_template('home.html', name=session['id'])


@main.route('/signup', methods = ['POST', 'GET'])
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

@main.route('/login' , methods = ['POST' , 'GET'])
def Login():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s AND password=%s', (id, password))
        record = cur.fetchone()
        if record:
            session['loggedin']= True
            session['id']= record[0]
            session['name'] = record[1]
            return redirect(url_for('home'))
        else:
            msg='Incorrect username/password. Try again!'
            return render_template('index.html', msg = msg)
    
    return render_template('signin.html')

@main.route('/room')
def room_status():
    user_id = session.get('id')

    if not user_id:
        return redirect(url_for('Login'))  # Redirect to login if user is not logged in

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the user has chosen a room
    cur.execute("SELECT number FROM rooms WHERE chosen_by = %s", (user_id,))
    chosen_room = cur.fetchone()

    if chosen_room:
        # Redirect to room_change if a room is already chosen
        return redirect(url_for('room_change_request'))
    else:
        # Redirect to room_list if no room is chosen
        return redirect(url_for('room_list'))

@main.route('/room-list')
def room_list():
    user_id = session.get('id')

    if not user_id:
        return redirect(url_for('Login'))  # Redirect to login if user is not logged in

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    return render_template('room_list.html', rooms=rooms)

@main.route('/feedback')
def feedback():
    # Implement the logic for feedback or redirect to a feedback page
    return "Feedback page (To be implemented)"

@main.route('/room_change_request')
def room_change_request():
    user_id = session.get('id')

    if not user_id:
        return redirect(url_for('Login'))  # Redirect to login if user is not logged in

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Retrieve the room number the user has chosen
    cur.execute("SELECT number FROM rooms WHERE chosen_by = %s", (user_id,))
    chosen_room = cur.fetchone()

    if chosen_room:
        room_number = chosen_room['number']
    else:
        room_number = None

    # Fetch all rooms for display
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()

    cur.close()

    return render_template('room_change.html', rooms=rooms, room_number=room_number)


@main.route('/choose-room', methods=['POST'])
def choose_room():
    user_id = session.get('id')

    if not user_id:
        return redirect(url_for('Login'))  # Redirect to login if the user ID is not in session

    room_number = request.form['room_number']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Verify that the user_id exists in the users table
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        return redirect(url_for('Login'))  # Redirect to login if user is invalid

    # Check if the room exists and is not already chosen
    cursor.execute("SELECT chosen_by FROM rooms WHERE number = %s", (room_number,))
    room = cursor.fetchone()

    if room and room['chosen_by'] is None:
        cursor.execute("UPDATE rooms SET chosen_by = %s WHERE number = %s", (user_id, room_number))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('room_change_request'))
    elif room:
        cursor.close()
        return redirect(url_for('room_list', error='Room is already chosen'))
    else:
        cursor.close()
        return redirect(url_for('room_list', error='Room not found'))

if __name__ == "__main__":
    main.run(debug=True) 