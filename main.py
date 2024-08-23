from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import bcrypt
import MySQLdb.cursors
import yaml

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
main.secret_key = 'terrychin'

mysql = MySQL(main)


@main.route('/')
def Index():
    return render_template('index.html')

@main.route('/signup' , methods = ['POST' , 'GET'])
def SignUp():
    if request.method == 'POST':
        userDetails = request.form
        username = userDetails['name']
        email = userDetails['email']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, password) VALUES(%s, %s , %s)", (username, email , password))
        mysql.connection.commit()
        cur.close()
        return ''
    return render_template('signup.html')


@main.route('/home')
def home():
    return render_template('home.html')

@main.route('/login' ,methods = ['POST' , 'GET'])
def Login():
    if request.method == 'POST':
        userDetails = request.form
        email = userDetails['email']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE email=%s AND password=%s', (email, password))
        record = cur.fetchone()
        if record:
            session['loggedin']= True
            session['email']= record[1]
            session['name'] = record[0]
            return redirect(url_for('home'))
        else:
            msg='Incorrect username/password. Try again!'
            return render_template('index.html', msg = msg)
        
        
    return render_template('signin.html')

if __name__ == "__main__":
    main.run(debug=True) 