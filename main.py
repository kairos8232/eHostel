from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
import MySQLdb.cursors
import yaml
import bcrypt
import os


main = Flask(__name__)


def create_main():
   main = Flask(__name__)
   main.config['SECRET_KEY'] = 'Hostel management secret key'
   return main
   

db = yaml.safe_load(open('db.yaml'))
main.config['MYSQL_HOST'] = db['mysql_host']
main.config['MYSQL_USER'] = db['mysql_user']
main.config['MYSQL_PASSWORD'] = db['mysql_password']
main.config['MYSQL_DB'] = db['mysql_db']
main.config['UPLOAD_FOLDER'] = db['mysql_profile_pic']
main.secret_key = 'terrychin'

mysql = MySQL(main)


@main.route('/')
def Index():
    return render_template('index.html')

@main.route("/home")
def home():
    return render_template('home.html')

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
        return redirect(url_for('home'))
    return render_template('signup.html')


@main.route('/login' ,methods = ['POST' , 'GET'])
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
            session['password'] = record[3]
            return redirect(url_for('home'))
        else:
            msg='Incorrect username/password. Try again!'
            return render_template('index.html', msg = msg)   

    return render_template('signin.html')


@main.route('/profile', methods=['GET', 'POST'])
def Profile():
    user_id = session.get('id')
    
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # name = request.form['name']
        gender = request.form['gender']
        email = request.form['email']
        profile_pic = request.files['image']
        
        if profile_pic:
            profile_pic_path = os.path.join(main.config['UPLOAD_FOLDER'], profile_pic.filename)
            profile_pic.save(profile_pic_path)
        else:
            profile_pic_path = None

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE users SET gender=%s, email=%s,  profile_pic=%s 
            WHERE id=%s
            """, (gender, email, profile_pic_path, user_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('Profile'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", [user_id])
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        user_profile = {
            'gender': user_data[2],
            'email': user_data[1],
            'image_url': url_for('static', filename=f"uploads/{user_data[4]}")
        }
        return render_template('profile.html', **user_profile)
    else:
        return redirect(url_for('home'))


@main.route('/register-hostel', methods = ['POST', 'GET'])
def Register():
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
