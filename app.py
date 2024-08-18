from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def Index():
    return render_template('index.html')

@app.route('/signup')
def SignUp():
    return render_template('signup.html')

@app.route('/login')
def Login():
    return render_template('signin.html')

if __name__ == "__main__":
    app.run(debug=True)
    