from flask import Flask, request, render_template, send_from_directory, session
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'your_secret_key_here'  # Required for session

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Default profile information
default_profile = {
    'name': 'John Doe',
    'title': 'Software Developer',
    'description': 'Passionate about creating elegant solutions to complex problems.',
    'image_url': '/static/default_profile.jpg'
}

@app.route('/', methods=['GET', 'POST'])
def profile_card():
    if 'profile' not in session:
        session['profile'] = default_profile.copy()

    if request.method == 'POST':
        session['profile']['name'] = request.form['name']
        session['profile']['title'] = request.form['title']
        session['profile']['description'] = request.form['description']
        
        image = request.files['image']
        if image and image.filename:  # Check if a new image was uploaded
            filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(filename)
            session['profile']['image_url'] = f'/uploads/{image.filename}'

        session.modified = True  # Ensure session is saved

    return render_template('profile.html', **session['profile'])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)