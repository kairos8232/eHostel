from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from functools import wraps
import MySQLdb.cursors
import yaml
from flask_bcrypt import Bcrypt
import os
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

# Check Admin Role
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin', False):
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Check Student Role
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('is_admin', False):
            flash('Access denied. This area is for students only.', 'error')
            return redirect(url_for('admin_dashboard'))
        if not session.get('loggedin', False):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

@main.route("/about")
def about():
    return render_template('about.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        password = userDetails['password']
        
        # First, try to authenticate as an admin
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM admin WHERE id=%s', (id,))
        user = cur.fetchone()
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['id'] = user['id']
            session['is_admin'] = True
            cur.close()
            return redirect(url_for('admin'))
        
        # If not an admin, try to authenticate as a student
        cur.execute('SELECT * FROM users WHERE id=%s', (id,))
        user = cur.fetchone()
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['id'] = user['id']
            session['is_admin'] = False
            cur.close()
            return redirect(url_for('home'))
        
        # If authentication fails for both admin and student
        cur.close()
        flash('Incorrect username/password. Try again!', 'error')
        return redirect(url_for('login'))
    
    return render_template('login.html')

#########################################STUDENT#############################################

#Student Home
@main.route("/student")
@student_required
def home():
    user_id = session.get('id')

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
    elif request.args.get('back'):
        current_index = (current_index - 1) % total_announcements
    
    session['announcement_index'] = current_index
    
    current_announcement = announcements[current_index] if announcements else None
    
    return render_template('home.html', 
                           announcement=current_announcement, 
                           has_next=total_announcements > 1,
                           has_back=total_announcements > 1,
                           invitation=invitation)

# Chatbox
@main.route("/student/chatbox")
@student_required
def chatbox():
    return render_template('chatbox.html')

# Student Profile
@main.route('/student/student/profile', methods=['GET', 'POST'])
@student_required
def profile():
    user_id = session.get('id')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    
    status = request.args.get('status')

    return render_template('profile.html',
        name=user[1],
        student_id=user[0],
        gender=user[2],
        email=user[3],
        faculty=user[5],
        image_url=user[6] or url_for('static', filename='default_profile.jpg'),
        url_for=url_for,
        status=status
    )

# Edit Profile
@main.route('/student/edit_profile', methods=['GET', 'POST'])
@student_required
def edit_profile():
    user_id = session.get('id')

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
@main.route('/student/change_password', methods=['GET', 'POST'])
@student_required
def change_password():
    user_id = session.get('id')

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
@main.route('/student/room_setting')
@student_required
def room_setting():
    user_id = session.get('id')

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

    cur.execute("""
                SELECT status
                FROM room_room_change_requests
                WHERE user_id = %
                ORDER BY request id DESC
                LIMIT 1
            """, (user_id,))
    request_status = cur.fetchone()

    # Fetch pending swap requests for this user
    cur.execute("""
        SELECT rsr.*, u.name AS requester_name, b.room_no AS requester_room, b.bed_number AS requester_bed
        FROM room_swap_requests rsr
        JOIN users u ON rsr.user_id = u.id
        JOIN booking b ON rsr.user_id = b.user_id
        WHERE rsr.other_user_id = %s AND rsr.status = 'pending'
    """, (user_id,))
    pending_swaps = cur.fetchall()
    
    cur.close()

    if not booking:
        return redirect(url_for('select_trimester'))

    status_message = None
    if request_status:
        if request_status['status'] == 'approved':
            status_message = "Room changed successfully"
        elif request_status['status'] == 'rejected':
            status_message = "Room change request rejected by admin"

    return render_template('room_setting.html', booking=booking, status_message=status_message, pending_swaps=pending_swaps)
    
# Select Trimester Route
@main.route('/student/select_trimester', methods=['GET', 'POST'])
@student_required
def select_trimester():  
      
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM trimester")
    trimesters = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        selected_trimester = request.form.get('trimester')
        session['trimester_id'] = selected_trimester
        return redirect(url_for('choose_mode'))

    return render_template('select_trimester.html', trimesters=trimesters)

# Mode selection route (Individual or Group)
@main.route('/choose_mode', methods=['GET', 'POST'])
@student_required
def choose_mode():
    
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
@main.route('/student/group', methods=['GET', 'POST'])
@student_required
def group_page():
    user_id = session.get('id')

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
@main.route('/student/manage_group/<int:group_id>', methods=['GET', 'POST'])
@student_required
def manage_group(group_id):
    user_id = session.get('id')

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
                    WHERE id = %s AND gender = %s AND id != %s
                    AND id NOT IN (
                        SELECT user_id FROM group_members
                    )
                """, (filter_student_id, leader_gender, user_id))
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
@main.route('/student/leave_group/<int:group_id>', methods=['POST'])
@student_required
def leave_group(group_id):
    user_id = session.get('id')

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
@main.route('/student/invite_user/<int:group_id>/<int:invitee_id>', methods=['POST'])
@student_required
def invite_user(group_id, invitee_id):
    user_id = session.get('id')  # User A (group leader) who is sending the invite

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
@main.route('/student/accept_invite/<int:invitation_id>', methods=['POST'])
@student_required
def accept_invite(invitation_id): 
    user_id = session.get('id')  # User B (invitee)
    
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
@main.route('/student/decline_invite/<int:invitation_id>', methods=['POST'])
@student_required
def decline_invite(invitation_id):
    user_id = session.get('id')  # User B (invitee)

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
@main.route('/student/select_hostel/<mode>', methods=['GET', 'POST'])
@student_required
def select_hostel(mode):
    user_id = session.get('id')

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
@main.route('/student/select_room_type/<mode>/<int:hostel_id>', methods=['GET', 'POST'])
@student_required
def select_room_type(mode, hostel_id):

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
@main.route('/student/select_bed/<mode>/<int:hostel_id>/<room_type>', methods=['GET', 'POST'])
@student_required
def select_bed(mode, hostel_id, room_type):
    user_id = session.get('id')

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
        
        # Always fetch the most up-to-date information from the database
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
@main.route('/student/booking_summary/<mode>/<int:hostel_id>/<room_type>/<int:room_number>/<bed_ids>/<user_ids>', methods=['GET', 'POST'])
@student_required
def booking_summary(mode, hostel_id, room_type, room_number, bed_ids, user_ids):
    user_id = session.get('id')

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
@main.route('/student/transfer_leadership/<int:group_id>/<int:new_leader_id>', methods=['POST'])
@student_required
def transfer_leadership(group_id, new_leader_id):
    user_id = session.get('id')

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
@main.route('/student/remove_member/<int:group_id>/<int:member_id>', methods=['POST'])
@student_required
def remove_member(group_id, member_id):
    user_id = session.get('id')

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
@main.route('/student/disband_group/<int:group_id>', methods=['POST'])
@student_required
def disband_group(group_id):
    user_id = session.get('id')

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

# Survey Start Route
@main.route('/student/survey', methods=['GET', 'POST'])
@student_required
def survey():
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
@main.route('/student/rate/<int:section_id>', methods=['GET', 'POST'])
@student_required
def survey_questions(section_id):
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
@main.route('/student/survey_done')
@student_required
def save_survey():
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

# Student Request Room Change
@main.route('/student/request_room_change', methods=['POST'])
@student_required
def request_room_change():
    user_id = session.get('id')
    reason = request.form.get('reason')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO room_change_requests (user_id, reason, status)
        VALUES (%s, %s, 'pending')
    """, (user_id, reason))
    mysql.connection.commit()
    cur.close()
    
    flash('Your room change request has been submitted.', 'success')
    return redirect(url_for('room_setting'))

@main.route('/student/submit_room_change', methods=['POST'])
@student_required
def submit_room_change():
    user_id = session.get('id')
    reason = request.form.get('reason')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO room_change_requests (user_id, reason, status)
        VALUES (%s, %s, 'pending')
    """, (user_id, reason))
    mysql.connection.commit()
    cur.close()
    
    flash('Your room change request has been submitted.', 'success')
    return redirect(url_for('room_setting'))

@main.route('/student/request_room_swap', methods=['POST'])
@student_required
def request_room_swap():
    user_id = session.get('id')
    other_student_id = request.form.get('other_student_id')
    other_student_email = request.form.get('other_student_email')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if the other student exists and has the same hostel
    cur.execute("""
        SELECT u.id, u.email, b.hostel_id, b.room_no, b.bed_number
        FROM users u
        JOIN booking b ON u.id = b.user_id
        WHERE u.id = %s AND u.email = %s
    """, (other_student_id, other_student_email))
    other_student = cur.fetchone()
    
    if not other_student:
        flash('No student found with the given ID and email.', 'error')
        return redirect(url_for('room_setting'))
    
    # Get current user's booking
    cur.execute("""
        SELECT hostel_id, room_no, bed_number
        FROM booking
        WHERE user_id = %s
        ORDER BY booking_no DESC
        LIMIT 1
    """, (user_id,))
    current_booking = cur.fetchone()
    
    if current_booking['hostel_id'] != other_student['hostel_id']:
        flash('Room swap is only allowed within the same hostel.', 'error')
        return redirect(url_for('room_setting'))
    
    cur.close()
    
    # If all checks pass, show the swap confirmation form
    return render_template('confirm_room_swap.html', other_student=other_student)

@main.route('/student/confirm_room_swap', methods=['POST'])
@student_required
def confirm_room_swap():
    user_id = session.get('id')
    other_student_id = request.form.get('other_student_id')
    reason = request.form.get('reason')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO room_swap_requests (user_id, other_user_id, reason, status)
        VALUES (%s, %s, %s, 'pending')
    """, (user_id, other_student_id, reason))
    mysql.connection.commit()
    cur.close()
    
    flash('Your room swap request has been submitted.', 'success')
    return redirect(url_for('room_setting'))

@main.route('/student/respond_to_swap', methods=['POST'])
@student_required
def respond_to_swap():
    user_id = session.get('id')
    swap_request_id = request.form.get('swap_request_id')
    response = request.form.get('response')
    
    cur = mysql.connection.cursor()
    if response == 'approve':
        cur.execute("""
            UPDATE room_swap_requests
            SET status = 'approved_by_student'
            WHERE id = %s AND other_user_id = %s
        """, (swap_request_id, user_id))
        flash('You have approved the room swap request. It will now be reviewed by the admin.', 'success')
    else:
        cur.execute("""
            UPDATE room_swap_requests
            SET status = 'rejected'
            WHERE id = %s AND other_user_id = %s
        """, (swap_request_id, user_id))
        flash('You have rejected the room swap request.', 'info')
    
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('room_setting'))

#########################################ADMIN#############################################

# Admin Home
@main.route("/admin")
@admin_required
def admin():
        return render_template('admin_page.html')

# Admin Signup Route (Implement to the Admin System) #########################################ADMIN#############################################
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

# Post Annoucement Route
@main.route('/admin/post_annoucement', methods=['GET', 'POST'])
@admin_required
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

# Admin Edit Trimester
@main.route('/admin/edit_trimester', methods=['GET', 'POST'])
@admin_required
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

# Admin Add Student
@main.route('/admin/add_student', methods=['GET', 'POST'])
@admin_required
def add_student():
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        userDetails = request.form
        id = userDetails['id']
        name = userDetails['name']
        gender = userDetails['gender']
        email = userDetails['email']
        password = userDetails['password']
        faculty = userDetails['faculty']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(id, name, gender, email, password, faculty) VALUES(%s, %s, %s, %s, %s, %s)", (id, name, gender, email, hashed_password, faculty))
        mysql.connection.commit()
        cur.close()
        flash('Student added successfully!')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users")
    students = cur.fetchall()
    cur.close()

    return render_template('add_student.html', students=students)

# Admin Delete Student
@main.route('/admin/delete_student/<student_id>', methods=['POST'])
def delete_student(student_id):
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (student_id,))
    mysql.connection.commit()
    cur.close()

    flash('Student deleted successfully!')
    return redirect(url_for('add_student'))

# Add room route
@main.route('/admin/add_room', methods=['GET', 'POST'])
@admin_required
def add_room():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute("SELECT id, name, gender FROM hostel")
    hostels = cur.fetchall()

    status_message = None  # Initialize status message variable

    if request.method == 'POST':
        number = request.form['number']
        hostel_id = request.form['hostel_id']
        category = request.form['category']
        price = request.form['price']
        status = 'Available'

        # Determine the capacity and corresponding bed letters based on the category
        if category == 'Single':
            capacity = 1
            beds = ['A']
        elif category == 'Double':
            capacity = 2
            beds = ['A', 'B']
        elif category == 'Triple':
            capacity = 3
            beds = ['A', 'B', 'C']

        # Check if the room number already exists
        cur.execute("SELECT * FROM rooms WHERE number = %s AND hostel_id = %s", (number, hostel_id))
        existing_room = cur.fetchone()

        if existing_room:
            status_message = f"Room number {number} already exists in this hostel."
        else:
            try:
                # Insert new room into the database
                cur.execute('''
                    INSERT INTO rooms (number, hostel_id, category, capacity, price, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (number, hostel_id, category, capacity, price, status))

                # Create beds for the room
                for bed in beds:
                    cur.execute('''
                        INSERT INTO beds (room_number, bed_letter, status)
                        VALUES (%s, %s, %s)
                    ''', (number, bed, 'Available'))

                mysql.connection.commit()
                status_message = 'Room and beds added successfully!'
            except mysql.connect.Error as err:
                mysql.connection.rollback()
                status_message = f"Error: {err}"
            finally:
                cur.close()

            return redirect(url_for('add_room'))

    # Render template and pass hostels and status_message to the form
    return render_template('room_add.html', hostels=hostels, status_message=status_message)

# Admin Edit Room
@main.route('/admin/edit_room/<int:room_number>', methods=['GET', 'POST'])
@admin_required
def edit_room(room_number):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch room details based on the room number
    cur.execute("SELECT * FROM rooms WHERE number = %s", (room_number,))
    room = cur.fetchone()

    if not room:
        flash("Room not found", "error")
        return redirect(url_for('rooms'))

    # Fetch all hostels for the dropdown
    cur.execute("SELECT id, name, gender FROM hostel")
    hostels = cur.fetchall()

    if request.method == 'POST':
        new_number = request.form['number']
        hostel_id = request.form['hostel_id']
        category = request.form['category']
        price = request.form['price']
        status = 'Available'

        # Determine the capacity based on the category
        capacity = {'Single': 1, 'Double': 2, 'Triple': 3}[category]

        # Check if the new room number already exists (if it's different from the current number)
        if int(new_number) != room_number:
            cur.execute("SELECT * FROM rooms WHERE number = %s", (new_number,))
            existing_room = cur.fetchone()
            if existing_room:
                flash(f"Room number {new_number} already exists.", "error")
                return render_template('room_edit.html', room=room, hostels=hostels)

        try:
            # Update room details in the database
            cur.execute('''
                UPDATE rooms 
                SET number = %s, hostel_id = %s, category = %s, capacity = %s, price = %s, status = %s
                WHERE number = %s
            ''', (new_number, hostel_id, category, capacity, price, status, room_number))

            # Update beds
            cur.execute("UPDATE beds SET room_number = %s WHERE room_number = %s", (new_number, room_number))

            # Adjust the number of beds if the category has changed
            cur.execute("SELECT COUNT(*) as bed_count FROM beds WHERE room_number = %s", (new_number,))
            current_beds = cur.fetchone()['bed_count']

            if current_beds < capacity:
                for i in range(current_beds, capacity):
                    bed_letter = chr(65 + i)  # A, B, C
                    cur.execute('''
                        INSERT INTO beds (room_number, bed_letter, status)
                        VALUES (%s, %s, 'Available')
                    ''', (new_number, bed_letter))
            elif current_beds > capacity:
                cur.execute("DELETE FROM beds WHERE room_number = %s ORDER BY bed_letter DESC LIMIT %s", 
                            (new_number, current_beds - capacity))

            mysql.connection.commit()
            flash('Room and beds updated successfully!', 'success')
            return redirect(url_for('edit_room', room_number=new_number))
        except MySQLdb.Error as err:
            mysql.connection.rollback()
            flash(f"Error: {err}", "error")

    cur.close()
    return render_template('room_edit.html', room=room, hostels=hostels)

# Admin Manage Rooms
@main.route('/admin/manage_rooms', methods=['GET', 'POST'])
@admin_required
def manage_rooms():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch all hostels for the filter dropdown
    cur.execute("SELECT id, name FROM hostel")
    hostels = cur.fetchall()

    # Fetch rooms based on the selected hostel filter
    selected_hostel_id = request.form.get('hostel_id') if request.method == 'POST' else None

    if selected_hostel_id and selected_hostel_id != 'all':
        # If a specific hostel is selected, filter rooms by hostel_id
        cur.execute('''SELECT rooms.*, hostel.name as hostel_name 
                       FROM rooms 
                       JOIN hostel ON rooms.hostel_id = hostel.id 
                       WHERE rooms.hostel_id = %s''', (selected_hostel_id,))
    else:
        # If 'All Hostels' is selected or no hostel is selected, fetch all rooms
        cur.execute('''SELECT rooms.*, hostel.name as hostel_name 
                       FROM rooms 
                       JOIN hostel ON rooms.hostel_id = hostel.id''')

    rooms = cur.fetchall()
    cur.close()

    # Render the template with rooms and hostels
    return render_template('room_manage.html', rooms=rooms, hostels=hostels, selected_hostel_id=selected_hostel_id)

# Admin Delete Room
@main.route('/admin/delete_room/<int:room_number>', methods=['POST'])
@admin_required
def delete_room(room_number):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Check if the room exists
        cur.execute('SELECT * FROM rooms WHERE number = %s', (room_number,))
        room = cur.fetchone()
        
        if not room:
            flash(f'Room {room_number} not found.', 'error')
            return redirect(url_for('manage_rooms'))

        # Delete associated beds first
        cur.execute('DELETE FROM beds WHERE room_number = %s', (room_number,))
        
        # Now delete the room
        cur.execute('DELETE FROM rooms WHERE number = %s', (room_number,))
        
        mysql.connection.commit()
        flash(f'Room {room_number} and associated beds deleted successfully!', 'success')
    except MySQLdb.Error as err:
        mysql.connection.rollback()
        flash(f"Error deleting room: {err}", 'error')
    finally:
        cur.close()

    return redirect(url_for('manage_rooms'))

# Admin Room Change Request Approval
@main.route('/admin/room_change_requests', methods=['GET', 'POST'])
@admin_required
def admin_room_change_requests():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        
        if action == 'approve':
            new_room_no = request.form.get('new_room_no')
            new_bed_letter = request.form.get('new_bed_letter')
            
            # Verify if the room and bed are still available
            cur.execute("""
                SELECT COUNT(*) as count
                FROM rooms r
                JOIN beds b ON r.number = b.room_number
                WHERE r.number = %s AND b.bed_letter = %s 
                AND (r.status = 'Available' OR r.status = 'Partially Occupied') AND b.status = 'Available'
            """, (new_room_no, new_bed_letter))
            result = cur.fetchone()
            
            if result['count'] > 0:
                # Get the current room and bed of the user
                cur.execute("""
                    SELECT room_no, bed_number
                    FROM booking
                    WHERE user_id = (SELECT user_id FROM room_change_requests WHERE request_id = %s)
                    ORDER BY booking_no DESC
                    LIMIT 1
                """, (request_id,))
                current_booking = cur.fetchone()
                
                # Update the booking
                cur.execute("""
                UPDATE booking
                SET room_no = %s, bed_number = %s
                WHERE user_id = (SELECT user_id FROM (SELECT user_id FROM room_change_requests WHERE request_id = %s) AS temp)
                AND booking_no = (SELECT MAX(booking_no) FROM (SELECT * FROM booking) AS b WHERE user_id = (SELECT user_id FROM room_change_requests WHERE request_id = %s));
                """, (new_room_no, new_bed_letter, request_id, request_id))
                
                # Update the new room and bed status
                cur.execute("UPDATE beds SET status = 'Occupied' WHERE room_number = %s AND bed_letter = %s", (new_room_no, new_bed_letter))
                
                # Update the old room and bed status
                cur.execute("UPDATE beds SET status = 'Available' WHERE room_number = %s AND bed_letter = %s", (current_booking['room_no'], current_booking['bed_number']))
                
                # Update room statuses
                update_room_status(cur, new_room_no)
                update_room_status(cur, current_booking['room_no'])
                
                # Update the request status
                cur.execute("UPDATE room_change_requests SET status = 'approved' WHERE request_id = %s", (request_id,))
                
                flash('Room change request approved successfully.', 'success')
            else:
                flash('The selected room or bed is no longer available. Please try again.', 'error')
        
        elif action == 'reject':
            # Update the request status
            cur.execute("UPDATE room_change_requests SET status = 'rejected' WHERE request_id = %s", (request_id,))
            flash('Room change request rejected.', 'success')
        
        mysql.connection.commit()

    # Fetch pending room change requests
    cur.execute("""
        SELECT rcr.*, u.name, u.email, b.room_no, b.bed_number, h.name as hostel_name, h.id as hostel_id
        FROM room_change_requests rcr
        JOIN users u ON rcr.user_id = u.id
        JOIN booking b ON u.id = b.user_id
        JOIN hostel h ON b.hostel_id = h.id
        WHERE rcr.status = 'pending'
        ORDER BY rcr.request_id ASC
    """)
    requests = cur.fetchall()
    
    # Fetch available rooms
    cur.execute("""
        SELECT r.number, r.hostel_id, h.name as hostel_name
        FROM rooms r
        JOIN hostel h ON r.hostel_id = h.id
        WHERE r.status IN ('Available', 'Partially Occupied')
        ORDER BY h.name, r.number
    """)
    available_rooms = cur.fetchall()
    
    # Fetch available beds for each available room
    available_beds = {}
    for room in available_rooms:
        cur.execute("""
            SELECT bed_letter
            FROM beds
            WHERE room_number = %s AND status = 'Available'
            ORDER BY bed_letter
        """, (room['number'],))
        available_beds[room['number']] = [bed['bed_letter'] for bed in cur.fetchall()]
    
    cur.close()
    
    return render_template('admin_room_change_requests.html', 
                           requests=requests, 
                           available_rooms=available_rooms, 
                           available_beds=available_beds)

def update_room_status(cur, room_number):
    cur.execute("""
        SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied
        FROM beds
        WHERE room_number = %s
    """, (room_number,))
    bed_status = cur.fetchone()
    
    if bed_status['occupied'] == 0:
        new_status = 'Available'
    elif bed_status['occupied'] == bed_status['total']:
        new_status = 'Occupied'
    else:
        new_status = 'Partially Occupied'
    
    cur.execute("UPDATE rooms SET status = %s WHERE number = %s", (new_status, room_number))

# Room Swap Request
@main.route('/admin/room_swap_requests')
@admin_required
def admin_room_swap_requests():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT rsr.*, 
               u1.name AS requester_name, u1.email AS requester_email,
               u2.name AS other_name, u2.email AS other_email,
               b1.room_no AS requester_room, b1.bed_number AS requester_bed,
               b2.room_no AS other_room, b2.bed_number AS other_bed,
               h.name AS hostel_name
        FROM room_swap_requests rsr
        JOIN users u1 ON rsr.user_id = u1.id
        JOIN users u2 ON rsr.other_user_id = u2.id
        JOIN booking b1 ON rsr.user_id = b1.user_id
        JOIN booking b2 ON rsr.other_user_id = b2.user_id
        JOIN hostel h ON b1.hostel_id = h.id
        WHERE rsr.status = 'approved_by_student'
        ORDER BY rsr.created_at ASC
    """)
    swap_requests = cur.fetchall()
    cur.close()
    
    return render_template('admin_room_swap_requests.html', swap_requests=swap_requests)

# Room Swap Process
@main.route('/admin/process_room_swap', methods=['POST'])
@admin_required
def process_room_swap():
    swap_request_id = request.form.get('swap_request_id')
    action = request.form.get('action')
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if action == 'approve':
        # Fetch the swap request details
        cur.execute("""
            SELECT user_id, other_user_id
            FROM room_swap_requests
            WHERE id = %s
        """, (swap_request_id,))
        swap_request = cur.fetchone()
        
        if swap_request:
            # Swap the rooms
            cur.execute("""
                UPDATE booking b1
                JOIN booking b2 ON b1.user_id = %s AND b2.user_id = %s
                SET b1.room_no = b2.room_no, b1.bed_number = b2.bed_number,
                    b2.room_no = b1.room_no, b2.bed_number = b1.bed_number
                WHERE b1.user_id = %s AND b2.user_id = %s
            """, (swap_request['user_id'], swap_request['other_user_id'], 
                  swap_request['user_id'], swap_request['other_user_id']))
            
            # Update the swap request status
            cur.execute("""
                UPDATE room_swap_requests
                SET status = 'approved_by_admin'
                WHERE id = %s
            """, (swap_request_id,))
            
            mysql.connection.commit()
            flash('Room swap has been approved and processed.', 'success')
        else:
            flash('Swap request not found.', 'error')
    
    elif action == 'reject':
        # Update the swap request status
        cur.execute("""
            UPDATE room_swap_requests
            SET status = 'rejected_by_admin'
            WHERE id = %s
        """, (swap_request_id,))
        
        # Set notification message for the requester
        cur.execute("""
            UPDATE users u
            JOIN room_swap_requests rsr ON u.id = rsr.user_id
            SET u.notification_message = 'Your room swap request has been rejected by the admin.'
            WHERE rsr.id = %s
        """, (swap_request_id,))
        
        mysql.connection.commit()
        flash('Room swap request has been rejected.', 'info')
    
    cur.close()
    return redirect(url_for('admin_room_swap_requests'))

@main.route('/admin/manage_sections', methods=['GET'])
@admin_required
def manage_sections():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM ques_sections ORDER BY id")
    sections = cur.fetchall()
    cur.close()
    return render_template('section_manage.html', sections=sections)

@main.route('/admin/manage_questions', methods=['GET'])
@admin_required
def manage_questions():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Fetch all sections for the dropdown
    cur.execute("SELECT * FROM ques_sections ORDER BY id")
    sections = cur.fetchall()
    
    # Fetch all questions with their corresponding section names
    cur.execute("""
        SELECT q.*, s.name as section_name 
        FROM questions q 
        JOIN ques_sections s ON q.section_id = s.id 
        ORDER BY s.id, q.id
    """)
    questions = cur.fetchall()
    
    cur.close()
    return render_template('question_manage.html', sections=sections, questions=questions)

@main.route('/admin/add_section', methods=['GET', 'POST'])
@admin_required
def add_section():
    if request.method == 'POST':
        section_name = request.form['section_name']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO ques_sections (name) VALUES (%s)", (section_name,))
        mysql.connection.commit()
        cur.close()
        flash('Section added successfully!', 'success')
        return redirect(url_for('manage_sections'))
    return render_template('section_add.html')

@main.route('/admin/edit_section/<int:section_id>', methods=['GET', 'POST'])
@admin_required
def edit_section(section_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        section_name = request.form['section_name']
        cur.execute("UPDATE ques_sections SET name = %s WHERE id = %s", (section_name, section_id))
        mysql.connection.commit()
        flash('Section updated successfully!', 'success')
        return redirect(url_for('manage_sections'))
    
    cur.execute("SELECT * FROM ques_sections WHERE id = %s", (section_id,))
    section = cur.fetchone()
    cur.close()
    return render_template('section_add.html', section=section)

@main.route('/admin/delete_section/<int:section_id>', methods=['POST'])
@admin_required
def delete_section(section_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM ques_sections WHERE id = %s", (section_id,))
    mysql.connection.commit()
    cur.close()
    flash('Section deleted successfully!', 'success')
    return redirect(url_for('manage_sections'))

@main.route('/admin/add_question', methods=['GET', 'POST'])
@admin_required
def add_question():
    if request.method == 'POST':
        section_id = request.form['section_id']
        question_text = request.form['question_text']
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO questions (section_id, text) 
            VALUES (%s, %s)
        """, (section_id, question_text))
        mysql.connection.commit()
        cur.close()
        flash('Question added successfully!', 'success')
        return redirect(url_for('add_question'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM ques_sections ORDER BY id")
    sections = cur.fetchall()
    cur.close()
    return render_template('question_add.html', sections=sections)

@main.route('/admin/edit_question/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        section_id = request.form['section_id']
        question_text = request.form['question_text']
        
        cur.execute("""
            UPDATE questions 
            SET section_id = %s, text = %s
            WHERE id = %s
        """, (section_id, question_text, question_id))
        mysql.connection.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('manage_questions'))
    
    cur.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
    question = cur.fetchone()
    cur.execute("SELECT * FROM ques_sections ORDER BY id")
    sections = cur.fetchall()
    cur.close()
    return render_template('question_edit.html', question=question, sections=sections)

@main.route('/admin/delete_question/<int:question_id>', methods=['POST'])
@admin_required
def delete_question(question_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM questions WHERE id = %s", (question_id,))
    mysql.connection.commit()
    cur.close()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('manage_questions'))

#####################################################################

# Logout Route
@main.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    main.run(debug=True)
