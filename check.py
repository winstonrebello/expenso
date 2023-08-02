# app.py
from flask import Flask, render_template,redirect, request,session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
# DB
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = "someRandomStringOfText"  # Change this to a secure random key


engine = create_engine("postgres://postgres:Winston()@localhost:5432/postgres")
db = scoped_session(sessionmaker(bind=engine)) 

# # Replace this dictionary with your actual user credentials or database validation logic.
# VALID_CREDENTIALS = {
#     'user1': 'password1',
#     'user2': 'password2',
# }

# Create a LoginForm using Flask-WTF
class RegisterForm(FlaskForm):
    username = StringField('username')
    password = PasswordField('password')
    submit = SubmitField('btnRegister')

@app.route('/')
def index():
    form = RegisterForm()  # Instantiate the form
    return render_template('register.html', form=form)  # Pass the form to the template

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
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

if __name__ == '__main__':
    app.run(debug=True)
