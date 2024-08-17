from flask import Flask, render_template

main = Flask(__name__)

@main.route('/')
def Index():
    return render_template('index.html')

@main.route('/signup')
def SignUp():
    return render_template('signup.html')

@main.route('/login')
def Login():
    return render_template('signin.html')

if __name__ == "__main__":
    main.run(debug=True)