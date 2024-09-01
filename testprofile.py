from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# This would typically come from a database
profile_data = {
    'name': 'Username',
    'image_url': '/static/images/anime-default-pfp-5.jpg',
    'gender': 'Male / Female',
    'contact': 'Contact Number',
    'email': 'Email Address',
    'biography': 'Anythings u can write...'
}

@app.route('/', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        profile_data['name'] = request.form['name']
        profile_data['gender'] = request.form['gender']
        profile_data['contact'] = request.form['contact']
        profile_data['email'] = request.form['email']
        profile_data['biography'] = request.form['biography']

        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_data['image_url'] = f'/static/uploads/{filename}'

        return redirect(url_for('profile'))

    return render_template('profile.html', **profile_data)

if __name__ == '__main__':
    app.run(debug=True)