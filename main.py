from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import yaml
from datetime import datetime

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
        return redirect(url_for("Login"))
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
            return redirect(url_for('choose_mode'))
        else:
            msg = 'Incorrect username/password. Try again!'
            return render_template('index.html', msg=msg)
    
    return render_template('signin.html')

# Mode selection route (Individual or Group)
@app.route('/choose-mode', methods=['GET', 'POST'])
def choose_mode():
    if 'loggedin' not in session:
        return redirect(url_for('Login'))
    if request.method == 'POST':
        mode = request.form['mode']
        if mode == 'individual':
            return redirect(url_for('select_hostel', mode='individual'))
        elif mode == 'group':
            return redirect(url_for('group_page'))
    return render_template('choose_mode.html')

# Group page route (Create or Join Group)
# Group page route (Create or Join Group)
@app.route('/group', methods=['GET', 'POST'])
def group_page():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Wrap 'groups' in backticks to avoid SQL syntax errors
    cur.execute("SELECT * FROM `groups` WHERE leader_id = %s", (user_id,))
    group = cur.fetchone()
    cur.close()

    if group:
        # Redirect to group management if already in a group
        return redirect(url_for('manage_group', group_id=group['group_id']))
    
    if request.method == 'POST':
        group_action = request.form['group_action']
        if group_action == 'create':
            # Create a new group and set current user as leader
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO `groups`(leader_id) VALUES(%s)", (user_id,))
            mysql.connection.commit()
            group_id = cur.lastrowid
            cur.execute("INSERT INTO group_members(group_id, user_id) VALUES(%s, %s)", (group_id, user_id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('manage_group', group_id=group_id))

    return render_template('group_page.html')


# Manage Group route
@app.route('/manage_group/<int:group_id>', methods=['GET', 'POST'])
def manage_group(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE group_id = %s AND leader_id = %s", (group_id, user_id))
    group = cur.fetchone()
    if not group:
        return redirect(url_for('group_page'))

    # Set group_id in session
    session['group_id'] = group_id

    cur.execute("SELECT users.id, users.email FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_members.group_id = %s", (group_id,))
    members = cur.fetchall()
    cur.close()

    return render_template('manage_group.html', members=members, group_id=group_id)



# Select Hostel Route
@app.route('/select_hostel/<mode>', methods=['GET', 'POST'])
def select_hostel(mode):
    print(f"Mode received: {mode}")  # Debugging line
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    if request.method == 'POST':
        hostel_id = request.form['hostel']
        return redirect(url_for('select_room_type', mode=mode, hostel_id=hostel_id))

    return render_template('select_hostel.html', mode=mode)

# Select Room Type Route
@app.route('/select_room_type/<mode>/<int:hostel_id>', methods=['GET', 'POST'])
def select_room_type(mode, hostel_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if mode == 'individual':
        cur.execute("SELECT DISTINCT category FROM rooms WHERE hostel_id = %s", (hostel_id,))
    elif mode == 'group':
        group_id = session.get('group_id')
        cur.execute("SELECT COUNT(*) as count FROM group_members WHERE group_id = %s", (group_id,))
        group_size = cur.fetchone()['count']
        
        # Add a debug print to help understand the flow
        print(f"Group size: {group_size}")
        
        if group_size == 2:
            cur.execute("SELECT DISTINCT category FROM rooms WHERE hostel_id = %s AND capacity >= 2", (hostel_id,))
        elif group_size == 3:
            cur.execute("SELECT DISTINCT category FROM rooms WHERE hostel_id = %s AND capacity >= 3", (hostel_id,))
        else:
            return render_template('error.html', message="No suitable room types available for your group size.")
    
    room_types = cur.fetchall()
    cur.close()

    if not room_types:
        return render_template('error.html', message="No suitable room types available for your group size.")
    
    if request.method == 'POST':
        room_type = request.form['room_type']
        return redirect(url_for('select_bed', mode=mode, hostel_id=hostel_id, room_type=room_type))

    return render_template('select_room_type.html', mode=mode, hostel_id=hostel_id, room_types=room_types)


# Select Bed Route
@app.route('/select_bed/<mode>/<int:hostel_id>/<room_type>', methods=['GET', 'POST'])
def select_bed(mode, hostel_id, room_type):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM rooms WHERE category = %s AND hostel_id = %s", (room_type, hostel_id))
    rooms = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        selected_room = request.form['selected_room']  # Make sure this matches the form field name
        datein = request.form['datein']
        dateout = request.form['dateout']
        cost = request.form['cost']

        if mode == 'individual':
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO booking(usersid, roomno, datein, dateout, cost) VALUES(%s, %s, %s, %s, %s)", (user_id, selected_room, datein, dateout, cost))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('booking_confirmation'))
        elif mode == 'group':
            group_id = session.get('group_id')
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO booking(usersid, roomno, datein, dateout, cost, group_id) VALUES(%s, %s, %s, %s, %s, %s)", (user_id, selected_room, datein, dateout, cost, group_id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('booking_confirmation'))
     
    return render_template('select_bed.html', rooms=rooms, mode=mode, hostel_id=hostel_id, room_type=room_type)

# Invite Member Route
@app.route('/invite_member/<int:group_id>', methods=['POST'])
def invite_member(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    email = request.form['email']

    # Check if the user exists
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    new_member = cur.fetchone()

    if not new_member:
        return render_template('error.html', message="User with this email does not exist.")

    # Check if the user is already in the group
    cur.execute("SELECT * FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, new_member['id']))
    if cur.fetchone():
        return render_template('error.html', message="This user is already a member of your group.")

    # Add the user to the group
    cur.execute("INSERT INTO group_members(group_id, user_id) VALUES(%s, %s)", (group_id, new_member['id']))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('manage_group', group_id=group_id))


# Booking Confirmation Route
@app.route('/booking_confirmation')
def booking_confirmation():
    return render_template('booking_confirmation.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    return redirect(url_for('Index'))

if __name__ == "__main__":
    app.run(debug=True)
