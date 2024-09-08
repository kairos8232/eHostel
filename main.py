from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import yaml
from flask_bcrypt import Bcrypt
import os
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
import hashlib

main = Flask(__name__)

# Load database configuration
db = yaml.safe_load(open('db.yaml'))
main.config['MYSQL_HOST'] = db['mysql_host']
main.config['MYSQL_USER'] = db['mysql_user']
main.config['MYSQL_PASSWORD'] = db['mysql_password']
main.config['MYSQL_DB'] = db['mysql_db']
main.config['UPLOAD_FOLDER'] = db['mysql_profile_pic']
main.secret_key = 'terrychin'
bcrypt = Bcrypt(main)
mysql = MySQL(main)

# Index route
@main.route('/')
def Index():
    return render_template('index.html')

# Sign-up route
@main.route('/signup', methods=['POST', 'GET'])
def SignUp():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        email = userDetails['email']
        gender = userDetails['gender']
        password = userDetails['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(id, email, gender, password) VALUES(%s, %s, %s, %s)", (id, email, gender, hashed_password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('home'))
    return render_template('signup.html')

# Login route
@main.route('/login', methods=['POST', 'GET'])
def Login():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s', (id,))
        record = cur.fetchone()
        if record and bcrypt.check_password_hash(record[3] , password):
            session['loggedin']= True
            session['id']= record[0]
            session['password'] = record[3]
            return redirect(url_for('home'))
        else:
            msg='Incorrect username/password. Try again!'
            return render_template('index.html', msg = msg)   

    return render_template('signin.html')

@main.route("/home")
def Home():
    return render_template('home.html')

@main.route('/profile', methods=['GET', 'POST'])
def Profile():
    user_id = session.get('id')
    
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # name = request.form['name']
        gender = request.form['gender']
        email = request.form['email']
        biography = request.form['biography']
        profile_pic = request.files['image']
        
        if profile_pic:
            profile_pic_path = os.path.join(main.config['UPLOAD_FOLDER'], profile_pic.filename)
            profile_pic.save(profile_pic_path)
        else:
            profile_pic_path = None

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE users SET gender=%s, email=%s,  profile_pic=%s, biography=%s
            WHERE id=%s
            """, (gender, email, profile_pic_path, biography, user_id))
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
            'image_url': url_for('static', filename=f"uploads/{user_data[4]}"),
            'biography': user_data[5]
        }
        return render_template('profile.html', **user_profile)
    else:
        return redirect(url_for('home'))

# Select Trimester Route
@main.route('/select_trimester', methods=['GET', 'POST'])
def select_trimester():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM trimester")
    trimesters = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        selected_trimester = request.form.get('trimester')
        session['trimester'] = selected_trimester
        return redirect(url_for('choose_mode'))

    return render_template('select_trimester.html', trimesters=trimesters)


@main.route('/edit_admin_trimester', methods=['GET', 'POST'])
def edit_trimester():
    if request.method == 'POST':
        userDetails = request.form
        trimesters = userDetails['semester']
        term = userDetails['term']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO trimester(name , term) VALUES(%s  , %s)", (trimesters,term))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('home'))
    return render_template('admin_trimester.html')


# Mode selection route (Individual or Group)
@main.route('/choose_mode', methods=['GET', 'POST'])
def choose_mode():
    if 'loggedin' not in session:
        return redirect(url_for('Login'))
    
    # Check if trimester is selected
    if 'trimester' not in session:
        return redirect(url_for('select_trimester'))

    user_id = session.get('id')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if user is in a group
    cur.execute("SELECT group_id FROM group_members WHERE user_id = %s", (user_id,))
    user_group = cur.fetchone()
    
    if user_group:
        # User is in a group, redirect to manage_group
        return redirect(url_for('manage_group', group_id=user_group['group_id']))

    if request.method == 'POST':
        mode = request.form['mode']
        if mode == 'individual':
            return redirect(url_for('select_hostel', mode='individual'))
        elif mode == 'group':
            return redirect(url_for('group_page'))

    cur.close()
    return render_template('choose_mode.html')

# Group page route (Create or Join Group)
@main.route('/group', methods=['GET', 'POST'])
def group_page():
    user_id = session.get('id')
    
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE leader_id = %s", (user_id,))
    group = cur.fetchone()
    cur.close()

    if group:
        return redirect(url_for('manage_group', group_id=group['group_id']))
    
    if request.method == 'POST':
        group_action = request.form['group_action']
        if group_action == 'create':
            selected_trimester = session.get('trimester')
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO `groups`(leader_id, trimester) VALUES(%s, %s)", (user_id, selected_trimester))
            mysql.connection.commit()
            group_id = cur.lastrowid
            cur.execute("INSERT INTO group_members(group_id, user_id) VALUES(%s, %s)", (group_id, user_id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('manage_group', group_id=group_id))

    return render_template('group_page.html')

# Manage Group route with student filtering
@main.route('/manage_group/<int:group_id>', methods=['GET', 'POST'])
def manage_group(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE group_id = %s AND leader_id = %s", (group_id, user_id))
    group = cur.fetchone()

    # Check if the user is a member of the group, regardless of whether they are the leader or not
    cur.execute("SELECT users.id, users.email FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_members.group_id = %s AND group_members.user_id = %s", (group_id, user_id))
    is_group_member = cur.fetchone()

    if not group and not is_group_member:
        return redirect(url_for('group_page'))

    session['group_id'] = group_id

    # Fetch all group members
    cur.execute("SELECT users.id, users.email FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_members.group_id = %s", (group_id,))
    members = cur.fetchall()

    students = None
    if request.method == 'POST':
        filter_student_id = request.form.get('filter_student_id')
        if filter_student_id:
            cur.execute("SELECT id, email FROM users WHERE id = %s AND id NOT IN (SELECT user_id FROM group_members WHERE group_id = %s)", (filter_student_id, group_id))
            students = cur.fetchall()
        else:
            students = []

    cur.close()

    return render_template('manage_group.html', members=members, group_id=group_id, students=students)

# Leave Group
@main.route('/leave_group/<int:group_id>', methods=['POST'])
def leave_group(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if the user is the leader
    cur.execute("SELECT leader_id FROM `groups` WHERE group_id = %s", (group_id,))
    group = cur.fetchone()
    
    if group and group['leader_id'] == user_id:
        return render_template('error.html', message="As the leader, you cannot leave the group. You must transfer leadership or disband the group.")

    # Remove the user from the group
    cur.execute("DELETE FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, user_id))
    mysql.connection.commit()
    
    # Check if the group is now empty
    cur.execute("SELECT COUNT(*) as count FROM group_members WHERE group_id = %s", (group_id,))
    member_count = cur.fetchone()['count']
    
    if member_count == 0:
        # If the group is empty, delete it
        cur.execute("DELETE FROM `groups` WHERE group_id = %s", (group_id,))
        mysql.connection.commit()

    cur.close()

    return redirect(url_for('choose_mode'))

# Select Hostel Route
@main.route('/select_hostel/<mode>', methods=['GET', 'POST'])
def select_hostel(mode):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM hostel")
    hostels = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        hostel_id = request.form['hostel']
        return redirect(url_for('select_room_type', mode=mode, hostel_id=hostel_id))

    return render_template('select_hostel.html', mode=mode, hostels=hostels)

# Select Room Type Route
@main.route('/select_room_type/<mode>/<int:hostel_id>', methods=['GET', 'POST'])
def select_room_type(mode, hostel_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if mode == 'individual':
        cur.execute("""
            SELECT r.*, COUNT(b.id) as total_beds, 
            SUM(CASE WHEN b.status = 'Available' THEN 1 ELSE 0 END) as available_beds
            FROM rooms r
            LEFT JOIN beds b ON r.number = b.room_number
            WHERE r.hostel_id = %s
            GROUP BY r.number
            HAVING available_beds > 0
        """, (hostel_id,))
    elif mode == 'group':
        group_id = session.get('group_id')
        cur.execute("SELECT COUNT(*) as count FROM group_members WHERE group_id = %s", (group_id,))
        group_size = cur.fetchone()['count']
        cur.execute("""
            SELECT r.*, COUNT(b.id) as total_beds, 
            SUM(CASE WHEN b.status = 'Available' THEN 1 ELSE 0 END) as available_beds
            FROM rooms r
            LEFT JOIN beds b ON r.number = b.room_number
            WHERE r.hostel_id = %s
            GROUP BY r.number
            HAVING available_beds >= %s
        """, (hostel_id, group_size))
    
    available_rooms = cur.fetchall()

    if request.method == 'POST':
        selected_room = request.form.get('room_number')
        if selected_room:
            return redirect(url_for('select_bed', mode=mode, hostel_id=hostel_id, room_type=available_rooms[0]['category'], selected_room=selected_room))

    cur.close()
    return render_template('select_room_type.html', mode=mode, hostel_id=hostel_id, available_rooms=available_rooms)

# Select Bed Route
@main.route('/select_bed/<mode>/<int:hostel_id>/<room_type>', methods=['GET', 'POST'])
def select_bed(mode, hostel_id, room_type):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    selected_room = request.args.get('selected_room')
    if not selected_room:
        return redirect(url_for('select_room_type', mode=mode, hostel_id=hostel_id))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT * FROM rooms WHERE number = %s", (selected_room,))
    room_info = cur.fetchone()
    if not room_info:
        cur.close()
        return render_template('error.html', message="Room not found.")

    cur.execute("SELECT * FROM beds WHERE room_number = %s AND status = 'Available'", (selected_room,))
    available_beds = cur.fetchall()

    group_id = session.get('group_id')
    group_members = []

    if mode == 'group' and group_id:
        cur.execute("SELECT users.id, users.name, users.email FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_members.group_id = %s", (group_id,))
        group_members = cur.fetchall()
    elif mode == 'individual':
        cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        current_user = cur.fetchone()
        group_members = [current_user] if current_user else []

    if request.method == 'POST':
        bed_assignments = {}
        for bed in available_beds:
            assigned_user_id = request.form.get(f'user_for_bed_{bed["id"]}')
            if assigned_user_id:
                bed_assignments[bed['id']] = int(assigned_user_id)

        if bed_assignments:
            bed_ids = ','.join(map(str, bed_assignments.keys()))
            user_ids = ','.join(map(str, bed_assignments.values()))
            return redirect(url_for('booking_summary', mode=mode, hostel_id=hostel_id, 
                                    room_type=room_type, room_number=selected_room, 
                                    bed_ids=bed_ids, user_ids=user_ids))

    cur.close()
    return render_template('select_bed.html', mode=mode, hostel_id=hostel_id, room_type=room_type, 
                           selected_room=selected_room, beds=available_beds, 
                           group_members=group_members, room_info=room_info)

# Booking Confirmation
@main.route('/booking_summary/<mode>/<int:hostel_id>/<room_type>/<int:room_number>/<bed_ids>/<user_ids>', methods=['GET', 'POST'])
def booking_summary(mode, hostel_id, room_type, room_number, bed_ids, user_ids):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM rooms WHERE number = %s", (room_number,))
    room_info = cur.fetchone()
    
    cur.execute("SELECT * FROM hostel WHERE id = %s", (hostel_id,))
    hostel_info = cur.fetchone()

    bed_id_list = bed_ids.split(',')
    user_id_list = user_ids.split(',')
    bed_assignments = []
    group_id = session.get('group_id') if mode == 'group' else None

    for bed_id, assigned_user_id in zip(bed_id_list, user_id_list):
        cur.execute("SELECT * FROM beds WHERE id = %s", (bed_id,))
        bed_info = cur.fetchone()
        
        cur.execute("SELECT * FROM users WHERE id = %s", (assigned_user_id,))
        user_info = cur.fetchone()
        
        bed_assignments.append({
            'bed': bed_info,
            'user': user_info if user_info else {'id': user_id, 'name': 'You'}
        })

    booking_details = {
        'hostel_name': hostel_info['name'],
        'room_number': room_number,
        'room_type': room_type,
        'price': room_info['price'],
        'bed_assignments': bed_assignments
    }

    if request.method == 'POST':
        trimester_id = session.get('trimester')

        for assignment in bed_assignments:
            cur.execute(
                "INSERT INTO booking(user_id, trimester_id, group_individual, group_id, hostel_id, room_no, bed_number, cost) "
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                (assignment['user']['id'], trimester_id, 1 if mode == 'group' else 0, group_id, hostel_id, room_number, assignment['bed']['bed_letter'], room_info['price'])
            )
            cur.execute("UPDATE beds SET status = 'Occupied' WHERE id = %s", (assignment['bed']['id'],))

        # Update room status if all beds are occupied
        cur.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied FROM beds WHERE room_number = %s", (room_number,))
        bed_status = cur.fetchone()
        if bed_status['total'] == bed_status['occupied']:
            cur.execute("UPDATE rooms SET status = 'Occupied' WHERE number = %s", (room_number,))
        else:
            cur.execute("UPDATE rooms SET status = 'Partially Occupied' WHERE number = %s", (room_number,))

        mysql.connection.commit()
        cur.close()

        return render_template('booking_success.html', message="Booking successful!")

    cur.close()

    return render_template('booking_summary.html', booking_details=booking_details, mode=mode, hostel_id=hostel_id, room_type=room_type, room_number=room_number, bed_ids=bed_ids)

# Invite Member Route
@main.route('/invite_member/<int:group_id>', methods=['POST'])
def invite_member(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    new_member_id = request.form['user_id']

    # Check if the user exists
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (new_member_id,))
    new_member = cur.fetchone()

    if not new_member:
        return render_template('error.html', message="User does not exist.")

    # Check if the user is already in the group
    cur.execute("SELECT * FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, new_member_id))
    if cur.fetchone():
        return render_template('error.html', message="This user is already a member of your group.")

    # Add the user to the group
    cur.execute("INSERT INTO group_members(group_id, user_id) VALUES(%s, %s)", (group_id, new_member_id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('manage_group', group_id=group_id))

# Transfer Leadership
@main.route('/transfer_leadership/<int:group_id>/<int:new_leader_id>', methods=['POST'])
def transfer_leadership(group_id, new_leader_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if the current user is the leader
    cur.execute("SELECT leader_id FROM `groups` WHERE group_id = %s", (group_id,))
    group = cur.fetchone()
    
    if not group or group['leader_id'] != user_id:
        cur.close()
        return render_template('error.html', message="You are not authorized to transfer leadership.")

    # Update the leader_id in the groups table
    cur.execute("UPDATE `groups` SET leader_id = %s WHERE group_id = %s", (new_leader_id, group_id))
    mysql.connection.commit()

    # If the current user was the leader, update the session data
    if user_id == session['id']:
        session['id'] = new_leader_id  # Update the session id to the new leader's id

    cur.close()

    # Redirect the user back to the manage_group page
    return redirect(url_for('manage_group', group_id=group_id))

# Remove Member
@main.route('/remove_member/<int:group_id>/<int:member_id>', methods=['POST'])
def remove_member(group_id, member_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE group_id = %s AND leader_id = %s", (group_id, user_id))
    group = cur.fetchone()
    if not group:
        return render_template('error.html', message="You are not the leader of this group.")

    cur.execute("DELETE FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, member_id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('manage_group', group_id=group_id))

# Disband Group
@main.route('/disband_group/<int:group_id>', methods=['POST'])
def disband_group(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('Login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE group_id = %s AND leader_id = %s", (group_id, user_id))
    group = cur.fetchone()
    if not group:
        return render_template('error.html', message="You are not the leader of this group.")

    cur.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
    cur.execute("DELETE FROM `groups` WHERE group_id = %s", (group_id,))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('choose_mode'))

# Logout Route
@main.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    return redirect(url_for('Index'))

if __name__ == "__main__":
    main.run(debug=True)

