from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

main = Flask(__name__)


db = db.load(open('db.yaml'))
main.config['MYSQL_HOST'] = db['mysql_host']
main.config['MYSQL_USER'] = db['mysql_user']
main.config['MYSQL_PASSWORD'] = db['mysql_password']
main.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(main)


@main.route('/')
def Index():
    return render_template('index.html')

@main.route('/signup')
def SignUp():
    if request.method == 'POST':
        userDetails = request.form
        username = userDetails['username']
        email = userDetails['email']
        password = userDetails['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(username, email, password) VALUES($s, $s)"), (username, email)
        mysql.connection.commit()
        cur.close()
        return 'success'
    return render_template('signup.html')

@main.route('/login')
def Login():
    if request.method == 'POST':
        userDetails = request.form
        email = userDetails['email']
        password = userDetails['password']
    return render_template('signin.html')

if __name__ == "__main__":
    main.run(debug=True) 