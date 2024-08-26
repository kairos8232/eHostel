from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import mysql.connector

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# This would typically come from a database
# profile_data = {
#     'name': 'Username',
#     'image_url': '/static/images/anime-default-pfp-5.jpg',
#     'contact': 'Contact Number',
#     'email': 'Email Address',
#     'biography': 'Anythings u can write...'
# }
# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database_name'
}
def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/', methods=['GET', 'POST'])
def profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        email = request.form['email']
        biography = request.form['biography']
        
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f'/static/uploads/{filename}'
            else:
                image_url = None
        else:
            image_url = None
        
        # Update the database
        update_query = """
        UPDATE user_profiles 
        SET name = %s, contact = %s, email = %s, biography = %s
        """
        update_data = (name, contact, email, biography)
        
        if image_url:
            update_query += ", image_url = %s"
            update_data += (image_url,)
        
        update_query += " WHERE id = %s"
        update_data += (1,)  # Assuming we're updating the profile with id 1
        
        cursor.execute(update_query, update_data)
        conn.commit()
        
        return redirect(url_for('profile'))
    
    # Fetch profile data from the database
    cursor.execute("SELECT * FROM user_profiles WHERE id = 1")
    profile_data = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('profile.html', **profile_data)

if __name__ == '__main__':
    app.run(debug=True)

# @app.route('/', methods=['GET', 'POST'])
# def profile():
#     if request.method == 'POST':
#         profile_data['name'] = request.form['name']
#         profile_data['contact'] = request.form['contact']
#         profile_data['email'] = request.form['email']
#         profile_data['biography'] = request.form['biography']

#         if 'image' in request.files:
#             file = request.files['image']
#             if file.filename != '':
#                 filename = secure_filename(file.filename)
#                 file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#                 profile_data['image_url'] = f'/static/uploads/{filename}'

#         return redirect(url_for('profile'))

#     return render_template('profile.html', **profile_data)

# if __name__ == '__main__':
#     app.run(debug=True)