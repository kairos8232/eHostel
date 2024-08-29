from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
import MySQLdb.cursors
import yaml

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Hostel management secret key'
    
    db = yaml.safe_load(open('db.yaml'))
    app.config['MYSQL_HOST'] = db['mysql_host']
    app.config['MYSQL_USER'] = db['mysql_user']
    app.config['MYSQL_PASSWORD'] = db['mysql_password']
    app.config['MYSQL_DB'] = db['mysql_db']
    
    mysql = MySQL(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/signup', methods=['POST', 'GET'])
    def signup():
        if request.method == 'POST':
            userDetails = request.form
            username = userDetails['name']
            email = userDetails['email']
            password = userDetails['password']
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            cur = mysql.connection.cursor()
            try:
                cur.execute("INSERT INTO users(name, email, password) VALUES(%s, %s, %s)", 
                            (username, email, hashed_password))
                mysql.connection.commit()
                flash('Account created successfully. Please log in.', 'success')
                return redirect(url_for('login'))
            except MySQLdb.IntegrityError:
                flash('Email already exists. Please use a different email.', 'error')
            finally:
                cur.close()
        return render_template('signup.html')

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            userDetails = request.form
            email = userDetails['email']
            password = userDetails['password']
            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            cur.close()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['loggedin'] = True
                session['email'] = user['email']
                session['name'] = user['name']
                return redirect(url_for('home'))
            else:
                flash('Incorrect email/password. Try again!', 'error')
        return render_template('login.html')

    @app.route('/home')
    def home():
        if 'loggedin' in session:
            return render_template('home.html', username=session['name'])
        return redirect(url_for('login'))

    @app.route('/logout')
    def logout():
        session.pop('loggedin', None)
        session.pop('email', None)
        session.pop('name', None)
        return redirect(url_for('index'))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)