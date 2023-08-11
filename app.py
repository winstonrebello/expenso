# DB
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
# flask
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from functools import wraps
#Security
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
# calling py
from find import login_required, apology,usd,convertSQLToDict
# Call helpers
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField

app = Flask(__name__)


app.secret_key = "someRandomStringOfText"
# otherwise pages will not open

# Enable CSRF protection globally for this app
csrf = CSRFProtect(app)

# Connection to DB
engine = create_engine("postgres://postgres:Winston()@localhost:5432/postgres")
db = scoped_session(sessionmaker(bind=engine)) 
# for thread safety, scoped session to separate user interactions with DB

class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('username')
    password = PasswordField('password')
    submit = SubmitField('btnRegister')

@app.route("/register", methods=["GET", "POST"])
def register():

    form = RegisterForm()
    # User reached route via POST
    if request.method == "POST":
        # Query DB for all existing user names and make sure new username isn't already taken
        username = request.form.get("username").strip()
        existingUsers = db.execute(
            "SELECT username FROM users WHERE LOWER(username) = :username", {"username": username.lower()}).fetchone()
        if existingUsers:
            return render_template("register.html", username=username,form=form)
        
        # Ensure username was submitted
        if not username:
            error = "Must Provide Username"
            return render_template("register.html",form=form,error=error)

        # Ensure password was submitted
        password = request.form.get("password")
        if not password:
            error = "Must Provide Password"
            return render_template("register.html",form=form,error=error)

        # Insert user into the database
        hashedPass = generate_password_hash(password)
        now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        newUserID = db.execute("INSERT INTO users (username, hash, registerDate, lastLogin) VALUES (:username, :hashedPass, :registerDate, :lastLogin) RETURNING id",
                               {"username": username, "hashedPass": hashedPass, "registerDate": now, "lastLogin": now}).fetchone()[0]
        db.commit()

        # Create default spending categories for user
        db.execute("INSERT INTO userCategories (category_id, user_id) VALUES (1, :usersID), (2, :usersID), (3, :usersID), (4, :usersID), (5, :usersID), (6, :usersID), (7, :usersID), (8, :usersID)",
                   {"usersID": newUserID})
        db.commit()

        # Auto-login the user after creating their username
        session["user_id"] = newUserID

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("register.html", form=form)
 
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    # remove any user_id
    session.clear()

    form = LoginForm()  # Instantiate the form again to access the submitted data

    if request.method == "POST":
        

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "Must Provide Username"
            return render_template('login.html', form=form,error=error)
            # return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Must Provide Password"
            return render_template('login.html', form=form,error=error)
        
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "Invalid Username and/or Password"
            return render_template('login.html', form=form,error=error)
            # return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Record the login time
        now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        db.execute(
            "UPDATE users SET lastLogin = :lastLogin WHERE id = :usersID", {"lastLogin": now, "usersID": session["user_id"]})
        db.commit()

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("login.html", form=form)

@app.route("/")
@login_required
def dashbaord():
    return render_template('index.html')

@app.route("/expenses", methods=["GET"])
@login_required
def expenses():
    """Manage expenses"""

    return render_template("expenses.html")

# main driver function
if __name__ == '__main__':
 
    # run() method of Flask class runs the application
    # on the local development server.
    app.run()

