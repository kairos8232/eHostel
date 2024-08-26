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
    return render_template('home.html', name = session['id'])

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
def room_list():
    # Use the MySQL connection from flask_mysqldb
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch room data from the database
    cur.execute("SELECT number, category, capacity, status, cost FROM rooms")
    rooms = cur.fetchall()

    # Close database connection
    cur.close()

    # Render the HTML template with the room data
    return render_template('room.html', rooms=rooms)

@main.route('/choose-room', methods=['POST'])
def choose_room():
    print("Session data before choosing room:", session)  # Debugging: Check session before proceeding
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
        return redirect(url_for('room_list', success='Room chosen successfully'))
    elif room:
        cursor.close()
        return redirect(url_for('room_list', error='Room is already chosen'))
    else:
        cursor.close()
        return redirect(url_for('room_list', error='Room not found'))

    # Fallback in case of unexpected behavior
    cursor.close()
    return redirect(url_for('room_list'))


if __name__ == "__main__":
    main.run(debug=True) 