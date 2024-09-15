from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import yaml
from flask_bcrypt import Bcrypt
import os
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
import hashlib
from scipy.spatial.distance import cosine
import numpy as np

main = Flask(__name__)

db = yaml.safe_load(open('db.yaml'))
main.config['MYSQL_HOST'] = db['mysql_host']
main.config['MYSQL_USER'] = db['mysql_user']
main.config['MYSQL_PASSWORD'] = db['mysql_password']
main.config['MYSQL_DB'] = db['mysql_db']
main.config['UPLOAD_FOLDER'] = db['mysql_profile_pic']
main.secret_key = 'terrychin'
bcrypt = Bcrypt(main)
mysql = MySQL(main)

# Get image url, to ensure every route catch the profile picture correctly
@main.context_processor
def inject_profile_pic():
    if 'id' in session:
        return {'profile_pic_url': get_profile_pic_url(session['id'])}
    return {}

def get_profile_pic_url(user_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT profile_pic FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return user['profile_pic'] if user and user['profile_pic'] else url_for('static', filename='images/default_profile_pic.jpg')

# Comparision between User and User
def calculate_similarity(ratings1, ratings2):
    v1 = np.array(ratings1)    # Convert ratings to numpy arrays
    v2 = np.array(ratings2)
    
    similarity = (1 - cosine(v1, v2))*100     # Calculate cosine similarity
    return similarity

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/student_login', methods=['POST', 'GET'])
def student_login():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s', (id,))
        record = cur.fetchone()
        if record and bcrypt.check_password_hash(record[4] , password):
            session['loggedin']= True
            session['id']= record[0]
            session['password'] = record[4]
            return redirect(url_for('home'))
        else:
            msg='Incorrect username/password. Try again!'
            return render_template('index.html', msg = msg)   
        
    return render_template('s-login.html')

@main.route('/admin', methods=['POST', 'GET'])
def admin_login():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE id=%s', (id,))
        record = cur.fetchone()
        if record and bcrypt.check_password_hash(record[4] , password):
            session['loggedin']= True
            session['id']= record[0]
            session['password'] = record[4]
            return redirect(url_for('home'))
        else:
            msg='Incorrect username/password. Try again!'
            return render_template('index.html', msg = msg)   

    return render_template('a-login.html')

@main.route("/home")
def home():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    # Fetch any pending invitations for this user
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT invitations.invitation_id, `groups`.name AS group_name, users.name AS leader_name
        FROM invitations
        JOIN `groups` ON invitations.group_id = `groups`.group_id
        JOIN users ON invitations.inviter_id = users.id
        WHERE invitee_id = %s AND status = 'pending'
    """, (user_id,))
    invitation = cur.fetchone()

    # Fetch announcements
    cur.execute("SELECT * FROM announcement ORDER BY id DESC")
    announcements = cur.fetchall()
    cur.close()

    current_index = session.get('announcement_index', 0)
    total_announcements = len(announcements)

    if request.args.get('next'):
        current_index = (current_index + 1) % total_announcements
        session['announcement_index'] = current_index

    current_announcement = announcements[current_index] if announcements else None

    return render_template('home.html', announcement=current_announcement, has_next=total_announcements > 1, invitation=invitation)

@main.route("/admin_page")
def admin():
        return render_template('admin_page.html')

# Admin Signup Route
@main.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        name = userDetails['name']
        email = userDetails['email']
        password = userDetails['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO admin(id, name, email, password) VALUES(%s, %s, %s, %s)", (id, name, email, hashed_password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin'))
    return render_template('signup.html')

# Student Profile Route
@main.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('id')
   
    if not user_id:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        session.pop('id', None)
        cur.close()
        return redirect(url_for('login'))
    
    status = request.args.get('status')

    return render_template('profile.html',
        name=user[1],
        student_id=user[0],
        gender=user[2],
        email=user[3],
        faculty=user[5],
        image_url=user[6] or url_for('static', filename='images/default_profile_pic.jpg'),
        url_for=url_for,
        status=status
    )

# Edit Profile
@main.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user_id = session.get('id')
    
    if not user_id:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        email = request.form['email']
        profile_pic = request.files.get('profile_pic')

        if profile_pic:
            profile_pic_path = os.path.join(main.config['UPLOAD_FOLDER'], profile_pic.filename)
            profile_pic.save(profile_pic_path)
            profile_pic_url = url_for('static', filename=f"uploads/{profile_pic.filename}")
        else:
            profile_pic_url = None

        cur.execute("""
            UPDATE users SET email=%s, profile_pic=%s
            WHERE id=%s
            """, (email, profile_pic_url, user_id))
        mysql.connection.commit()
        return redirect(url_for('profile'))

    cur.execute("SELECT name, id, gender, faculty, email, profile_pic FROM users WHERE id=%s", [user_id])
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        user_profile = {
            'name': user_data['name'],
            'student_id': user_data['id'],
            'gender': user_data['gender'],
            'faculty': user_data['faculty'],
            'email': user_data['email'],
            'image_url': user_data['profile_pic'] if user_data['profile_pic'] else url_for('static', filename='images/default_profile_pic.jpg')
        }

        return render_template('edit_profile.html', **user_profile)
    else:
        return redirect(url_for('home'))

# Change Password Route
@main.route('/change_password', methods=['GET', 'POST'])
def change_password():
    user_id = session.get('id')
    
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM users WHERE id=%s", [user_id])
        user_data = cur.fetchone()
        cur.close()

        if user_data and bcrypt.check_password_hash(user_data[0], current_password):
            if new_password == confirm_password:
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_password, user_id))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('profile', status='success'))
            else:
                return redirect(url_for('change_password', error='Passwords do not match.'))
        else:
            return redirect(url_for('change_password', error='Current password is incorrect.'))

    error = request.args.get('error')
    status = request.args.get('status')
    return render_template('change_password.html', error=error, status=status)

# Room Setting
@main.route('/room_setting')
def room_setting():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT b.*, h.name as hostel_name, r.category as room_type
        FROM booking b
        JOIN hostel h ON b.hostel_id = h.id
        JOIN rooms r ON b.room_no = r.number
        WHERE b.user_id = %s
        ORDER BY b.booking_no DESC
        LIMIT 1
    """, (user_id,))
    booking = cur.fetchone()
    cur.close()

    if not booking:
        return redirect(url_for('select_trimester'))

    return render_template('room_setting.html', booking=booking)

# Post Annoucement Route
@main.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        userDetails = request.form
        title = userDetails['title']
        context = userDetails['context']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO announcement(title, context) VALUES(%s  , %s)", (title, context))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('home'))
  
    return render_template('post_announcement.html')
    
# Select Trimester Route
@main.route('/select_trimester', methods=['GET', 'POST'])
def select_trimester():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM trimester")
    trimesters = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        selected_trimester = request.form.get('trimester')
        session['trimester_id'] = selected_trimester
        return redirect(url_for('choose_mode'))

    return render_template('select_trimester.html', trimesters=trimesters)

# Admin Edit Trimester
@main.route('/edit_admin_trimester', methods=['GET', 'POST'])
def edit_trimester():
    if request.method == 'POST':
        userDetails = request.form
        trimesters = userDetails['semester']
        term = userDetails['term']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO trimester(name, term) VALUES(%s  , %s)", (trimesters, term))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('home'))
    return render_template('admin_trimester.html')

# Mode selection route (Individual or Group)
@main.route('/choose_mode', methods=['GET', 'POST'])
def choose_mode():
    if 'loggedin' not in session:
        return redirect(url_for('student_login'))
    
    if 'trimester_id' not in session:
        return redirect(url_for('select_trimester'))
    
    user_id = session.get('id')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT group_id FROM group_members WHERE user_id = %s", (user_id,))
    user_group = cur.fetchone()
    
    if user_group:
        session['group_id'] = user_group['group_id']
        return redirect(url_for('manage_group', group_id=user_group['group_id']))

    if request.method == 'POST':
        mode = request.form['mode']
        if mode == 'individual':
            session['group_id'] = None
            return redirect(url_for('select_hostel', mode='individual'))
        elif mode == 'group':
            cur.execute("SELECT group_id FROM group_members WHERE user_id = %s", (user_id,))
            user_group = cur.fetchone()
            if user_group:
                session['group_id'] = user_group['group_id']
            return redirect(url_for('group_page'))

    cur.close()
    return render_template('choose_mode.html')

# Group page route (Create or Join Group)
@main.route('/group', methods=['GET', 'POST'])
def group_page():
    user_id = session.get('id')
    
    if not user_id:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE leader_id = %s", (user_id,))
    group = cur.fetchone()
    cur.close()

    if group:
        return redirect(url_for('manage_group', group_id=group['group_id']))
    
    if request.method == 'POST':
        group_action = request.form['group_action']
        if group_action == 'create':
            selected_trimester = session.get('trimester_id')

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO `groups`(leader_id, trimester_id) VALUES(%s, %s)", (user_id, selected_trimester))
            mysql.connection.commit()
            group_id = cur.lastrowid
            cur.execute("INSERT INTO group_members(group_id, user_id) VALUES(%s, %s)", (group_id, user_id))
            mysql.connection.commit()
            cur.close()
            session['group_id'] = group_id
            return redirect(url_for('manage_group', group_id=group_id))

    return render_template('group_page.html')

# Manage Group route with student filtering and suggested roommate
@main.route('/manage_group/<int:group_id>', methods=['GET', 'POST'])
def manage_group(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE group_id = %s AND leader_id = %s", (group_id, user_id))
    group = cur.fetchone()

    cur.execute("SELECT users.id, users.email FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_members.group_id = %s AND group_members.user_id = %s", (group_id, user_id))
    is_group_member = cur.fetchone()

    if not group and not is_group_member:
        return redirect(url_for('group_page'))

    cur.execute("SELECT * FROM `groups` WHERE group_id = %s", (group_id,))
    group = cur.fetchone()

    if not group:
        cur.close()
        return render_template('error.html', message="Group not found.")

    is_leader = group['leader_id'] == user_id

    cur.execute("SELECT gender FROM users WHERE id = %s", (group['leader_id'],))
    leader_gender = cur.fetchone()['gender']

    cur.execute("""
        SELECT users.id, users.email, users.name, users.faculty, users.gender,
               CASE WHEN users.id = groups.leader_id THEN 1 ELSE 0 END as is_leader
        FROM users 
        JOIN group_members ON users.id = group_members.user_id 
        JOIN `groups` ON group_members.group_id = groups.group_id
        WHERE group_members.group_id = %s
    """, (group_id,))
    members = cur.fetchall()

    students = None
    if request.method == 'POST':
        if 'suggest_roommates' in request.form:
            # Get the current user's ratings
            cur.execute("SELECT rating FROM user_ratings WHERE user_id = %s ORDER BY question_id", (user_id,))
            user_ratings = [rating['rating'] for rating in cur.fetchall()]

            # Get all other users of the same gender who are not in the group
            cur.execute("""
                SELECT id, name, faculty, gender
                FROM users
                WHERE gender = %s AND id != %s AND id NOT IN (
                    SELECT user_id FROM group_members WHERE group_id = %s
                )
            """, (leader_gender, user_id, group_id))
            potential_roommates = cur.fetchall()

            # Calculate similarity for each potential roommate
            students = []
            for roommate in potential_roommates:
                cur.execute("SELECT rating FROM user_ratings WHERE user_id = %s ORDER BY question_id", (roommate['id'],))
                roommate_ratings = [rating['rating'] for rating in cur.fetchall()]
                
                if len(user_ratings) == len(roommate_ratings):
                    similarity = calculate_similarity(user_ratings, roommate_ratings)
                    roommate['similarity'] = round(similarity, 2)  # Round to 2 decimal places
                    students.append(roommate)

            # Sort by similarity (highest first) and take top 10
            students = sorted(students, key=lambda x: x['similarity'], reverse=True)[:10]
            print(students)  # Print the list of students and their similarity values

        elif 'filter_student_id' in request.form:
            filter_student_id = request.form.get('filter_student_id')
            if filter_student_id:
                cur.execute("""
                    SELECT id, name, faculty, gender
                    FROM users
                    WHERE id = %s AND gender = %s AND id NOT IN (
                        SELECT user_id FROM group_members WHERE group_id = %s
                    )
                """, (filter_student_id, leader_gender, group_id))
                students = cur.fetchall()

                if students:
                    # Calculate similarity for the found student
                    cur.execute("SELECT rating FROM user_ratings WHERE user_id = %s ORDER BY question_id", (user_id,))
                    user_ratings = [rating['rating'] for rating in cur.fetchall()]

                    cur.execute("SELECT rating FROM user_ratings WHERE user_id = %s ORDER BY question_id", (students[0]['id'],))
                    student_ratings = [rating['rating'] for rating in cur.fetchall()]

                    if len(user_ratings) == len(student_ratings):
                        similarity = calculate_similarity(user_ratings, student_ratings)
                        students[0]['similarity'] = round(similarity, 2)  # Round to 2 decimal places
                    else:
                        students[0]['similarity'] = 0
            else:
                students = []

    cur.close()

    return render_template('manage_group.html', members=members, group_id=group_id, students=students, is_leader=is_leader, current_user_id=user_id, leader_gender=leader_gender)

# Leave Group
@main.route('/leave_group/<int:group_id>', methods=['POST'])
def leave_group(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

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

# Invite Member Route
@main.route('/invite_user/<int:group_id>/<int:invitee_id>', methods=['POST'])
def invite_user(group_id, invitee_id):
    user_id = session.get('id')  # User A (group leader) who is sending the invite
    if not user_id:
        return redirect(url_for('student_login'))

    # Insert the invitation into the 'invitations' table
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO invitations (group_id, inviter_id, invitee_id, status)
        VALUES (%s, %s, %s, 'pending')
    """, (group_id, user_id, invitee_id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('manage_group', group_id=group_id))

# Accept the invitation
@main.route('/accept_invite/<int:invitation_id>', methods=['POST'])
def accept_invite(invitation_id):
    
    user_id = session.get('id')  # User B (invitee)
    if not user_id:
        return redirect(url_for('student_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Update invitation status to 'accepted'
    cur.execute("""
        UPDATE invitations
        SET status = 'accepted'
        WHERE invitation_id = %s AND invitee_id = %s
    """, (invitation_id, user_id))

    # Fetch the group_id from the invitation
    cur.execute("SELECT group_id FROM invitations WHERE invitation_id = %s", (invitation_id,))
    group = cur.fetchone()

    # Add the user to the group members
    cur.execute("""
        INSERT INTO group_members (group_id, user_id)
        VALUES (%s, %s)
    """, (group['group_id'], user_id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('manage_group', group_id=group['group_id']))

# Decline the invitation
@main.route('/decline_invite/<int:invitation_id>', methods=['POST'])
def decline_invite(invitation_id):
    user_id = session.get('id')  # User B (invitee)
    if not user_id:
        return redirect(url_for('student_login'))

    cur = mysql.connection.cursor()

    # Update invitation status to 'declined'
    cur.execute("""
        UPDATE invitations
        SET status = 'declined'
        WHERE invitation_id = %s AND invitee_id = %s
    """, (invitation_id, user_id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('home'))

# Select Hostel Route
@main.route('/select_hostel/<mode>', methods=['GET', 'POST'])
def select_hostel(mode):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get user's gender
    cur.execute("SELECT gender FROM users WHERE id = %s", (user_id,))
    user_gender = cur.fetchone()['gender']

    # Get hostels matching the user's gender
    cur.execute("SELECT * FROM hostel WHERE gender = %s", (user_gender,))
    hostels = cur.fetchall()

    if request.method == 'POST':
        selected_hostel_id = request.form.get('hostel')
        if selected_hostel_id:
            hostel_id = int(selected_hostel_id)
            session['hostel_id'] = hostel_id
            return redirect(url_for('select_room_type', mode=mode, hostel_id=hostel_id))

    cur.close()
    return render_template('select_hostel.html', mode=mode, hostels=hostels)

# Select Room Type Route
@main.route('/select_room_type/<mode>/<int:hostel_id>', methods=['GET', 'POST'])
def select_room_type(mode, hostel_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    group_id = session.get('group_id')

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
    return render_template('select_room_type.html', mode=mode, hostel_id=hostel_id, available_rooms=available_rooms, group_id=group_id)

# Select Bed Route
@main.route('/select_bed/<mode>/<int:hostel_id>/<room_type>', methods=['GET', 'POST'])
def select_bed(mode, hostel_id, room_type):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    selected_room = request.args.get('selected_room')
    if not selected_room:
        return redirect(url_for('select_room_type', mode=mode, hostel_id=hostel_id))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        cur.execute("SELECT * FROM rooms WHERE number = %s", (selected_room,))
        room_info = cur.fetchone()
        if not room_info:
            raise ValueError("Room not found.")

        cur.execute("SELECT * FROM beds WHERE room_number = %s AND status = 'Available'", (selected_room,))
        available_beds = cur.fetchall()

        group_id = session.get('group_id')
        
        if mode == 'group' and group_id:
            cur.execute("""
                SELECT users.id, users.name, users.email 
                FROM users 
                JOIN group_members ON users.id = group_members.user_id 
                WHERE group_members.group_id = %s
            """, (group_id,))
            group_members = cur.fetchall()
        elif mode == 'individual':
            cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
            current_user = cur.fetchone()
            group_members = [current_user] if current_user else []
        else:
            group_members = []

        assigned_users = []

        if request.method == 'POST':
            bed_assignments = {}
            for bed in available_beds:
                assigned_user_id = request.form.get(f'user_for_bed_{bed["id"]}')
                if assigned_user_id:
                    bed_assignments[bed['id']] = int(assigned_user_id)
                    assigned_users.append(str(assigned_user_id))

            if bed_assignments:
                bed_ids = ','.join(map(str, bed_assignments.keys()))
                user_ids = ','.join(map(str, bed_assignments.values()))
                return redirect(url_for('booking_summary', mode=mode, hostel_id=hostel_id, 
                                        room_type=room_type, room_number=selected_room, 
                                        bed_ids=bed_ids, user_ids=user_ids))
            
        return render_template('select_bed.html', mode=mode, hostel_id=hostel_id, room_type=room_type, 
                               selected_room=selected_room, beds=available_beds, 
                               group_members=group_members, room_info=room_info, assigned_users=assigned_users)

    except Exception as e:
        return render_template('error.html', message=f"An error occurred: {str(e)}")

    finally:
        cur.close()

# Booking Confirmation
@main.route('/booking_summary/<mode>/<int:hostel_id>/<room_type>/<int:room_number>/<bed_ids>/<user_ids>', methods=['GET', 'POST'])
def booking_summary(mode, hostel_id, room_type, room_number, bed_ids, user_ids):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

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

# Transfer Leadership
@main.route('/transfer_leadership/<int:group_id>/<int:new_leader_id>', methods=['POST'])
def transfer_leadership(group_id, new_leader_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

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

    session['group_id'] = group_id

    # Redirect the user back to the manage_group page
    return redirect(url_for('manage_group', group_id=group_id))

# Remove Member
@main.route('/remove_member/<int:group_id>/<int:member_id>', methods=['POST'])
def remove_member(group_id, member_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE group_id = %s AND leader_id = %s", (group_id, user_id))
    group = cur.fetchone()
    if not group:
        return render_template('error.html', message="You are not the leader of this group.")

    cur.execute("DELETE FROM group_members WHERE group_id = %s AND user_id = %s", (group_id, member_id))
    mysql.connection.commit()
    cur.close()

    session['group_id'] = group_id

    return redirect(url_for('manage_group', group_id=group_id))

# Disband Group
@main.route('/disband_group/<int:group_id>', methods=['POST'])
def disband_group(group_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    session.pop('group_id', None)
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM `groups` WHERE group_id = %s AND leader_id = %s", (group_id, user_id))
    group = cur.fetchone()
    if not group:
        return render_template('error.html', message="You are not the leader of this group.")

    cur.execute("DELETE FROM invitations WHERE group_id = %s", (group_id,))
    cur.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
    cur.execute("DELETE FROM `groups` WHERE group_id = %s", (group_id,))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('choose_mode'))

# Feedback route
@main.route('/feedback', methods=['POST'])
def feedback():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    feedback_text = request.form['feedback']
    # Save feedback to the database
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO feedback (user_id, feedback) VALUES (%s, %s)", (user_id, feedback_text))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('room_status'))

# Room change request route
@main.route('/request_room_change', methods=['POST'])
def request_room_change():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('student_login'))

    room_number = session.get('room_number')
    # Process room change request
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE booking SET status = 'Room Change Requested' WHERE usersid = %s AND roomno = %s", (user_id, room_number))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('room_status'))

# Survey Start Route
@main.route('/survey', methods=['GET', 'POST'])
def survey():
    if 'id' not in session:
        return redirect(url_for('login'))

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if the user has already completed the survey
    cursor.execute("SELECT survey_completed FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if user['survey_completed'] == 1:
        return render_template('survey_completed.html')

    if request.method == 'POST':
        # Get the first section
        cursor.execute("SELECT id FROM ques_sections ORDER BY id ASC LIMIT 1")
        first_section = cursor.fetchone()
        if first_section:
            return redirect(url_for('survey_questions', section_id=first_section['id']))
    
    return render_template('survey_start.html')

# Answer Survey Route
@main.route('/rate/<int:section_id>', methods=['GET', 'POST'])
def survey_questions(section_id):
    if 'id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Get all questions for the current section
    cursor.execute("SELECT * FROM questions WHERE section_id = %s", (section_id,))
    questions = cursor.fetchall()

    # Get section name
    cursor.execute("SELECT name FROM ques_sections WHERE id = %s", (section_id,))
    section = cursor.fetchone()
    section_name = section['name'] if section else "Unknown Section"

    # Check if this is the last section
    cursor.execute("SELECT id FROM ques_sections WHERE id > %s ORDER BY id ASC LIMIT 1", (section_id,))
    next_section = cursor.fetchone()
    is_last_section = next_section is None

    if request.method == 'POST':
        # Store ratings for all questions in the section
        for question in questions:
            rating = request.form.get(f'rating_{question["id"]}')
            if rating:
                cursor.execute("""
                    INSERT INTO user_ratings (user_id, question_id, rating) 
                    VALUES (%s, %s, %s) 
                    ON DUPLICATE KEY UPDATE rating = %s
                """, (session['id'], question['id'], rating, rating))
        mysql.connection.commit()

        if is_last_section:
            return redirect(url_for('save_survey'))
        else:
            return redirect(url_for('survey_questions', section_id=next_section['id']))

    return render_template('survey_questions.html', 
                           questions=questions, 
                           section_name=section_name,
                           section_id=section_id,
                           is_last_section=is_last_section)

# Done Survey Route
@main.route('/survey_done')
def save_survey():
    if 'id' not in session:
        return redirect(url_for('login'))

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Mark the survey as completed for this user
    cursor.execute("UPDATE users SET survey_completed = 1 WHERE id = %s", (user_id,))
    mysql.connection.commit()
    
    return render_template('survey_success.html')

# Get User Ratings
def get_user_ratings(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT rating FROM user_ratings WHERE user_id = %s ORDER BY question_id", (user_id,))
    ratings = cur.fetchall()
    cur.close()
    return [rating[0] for rating in ratings]

# Logout Route
@main.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    main.run(debug=True)

