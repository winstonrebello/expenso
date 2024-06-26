import os
import json
import requests
import copy
import calendar
import e_dashboard
import e_expenses
import e_analytics
import e_budgets
import e_categories
import tendie_reports
import e_account
import psycopg2

from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Set app key  pass @888Guns
app.secret_key = "someRandomStringOfText"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp() # only remove comment when testing locally for benefit of temp directories
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Custom filter
app.jinja_env.filters["usd"] = usd
# Enable CSRF protection globally for the Flask app
csrf = CSRFProtect(app)

# Create engine object to manage connections to DB, and scoped session to separate user interactions with DB
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


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show dashboard of budget/expenses"""

    # User reached route via GET
    if request.method == "GET":
        # TODO reduce or completely remove the redundant use of javascript code in dashboard.js and reports.js

        # Initialize metrics to None to render the appropriate UX if data does not exist yet for the user
        expenses_year = None
        expenses_month = None
        expenses_week = None
        expenses_last5 = None
        spending_week = []
        spending_month = []

        # Get the users spend categories (for quick expense modal)
        categories = e_categories.getSpendCategories(session["user_id"])

        # Get the users payers (for quick expense modal)
        payers = e_account.getPayers(session["user_id"])

        # Get todays date (for quick expense modal)
        date = datetime.today().strftime('%Y-%m-%d')

        # Get the users income
        income = e_account.getIncome(session["user_id"])

        # Get current years total expenses for the user
        expenses_year = e_dashboard.getTotalSpend_Year(session["user_id"])
        
        Month_number = db.execute("SELECT to_char(current_date, 'MM')::int as month_no limit 1").fetchone()

        if Month_number is not None:
            Month_number = Month_number[0]
        else:
            Month_number = 1

        # Get current months total expenses for the user
        expenses_month = e_dashboard.getTotalSpend_Month(
            session["user_id"])

        # Get current week total expenses for the user
        expenses_week = e_dashboard.getTotalSpend_Week(session["user_id"])

        # Get last 5 expenses for the user
        expenses_last5 = e_dashboard.getLastFiveExpenses(
            session["user_id"])

        # Get every budgets spent/remaining for the user
        budgets = e_dashboard.getBudgets(session["user_id"])

        # Get weekly spending for the user
        weeks = e_dashboard.getLastFourWeekNames()
        spending_week = e_dashboard.getWeeklySpending(
            weeks, session["user_id"])

        # Get monthly spending for the user (for the current year)
        spending_month = e_dashboard.getMonthlySpending(
            session["user_id"])

        # Get spending trends for the user
        spending_trends = e_dashboard.getSpendingTrends(
            session["user_id"])

        # Get payer spending for the user
        payersChart = tendie_reports.generatePayersReport(session["user_id"])

        return render_template("index.html", categories=categories, payers=payers, date=date, income=income, expenses_year=expenses_year, expenses_month=expenses_month, expenses_week=expenses_week, expenses_last5=expenses_last5,
                               budgets=budgets, spending_week=spending_week, spending_month=spending_month, spending_trends=spending_trends, payersChart=payersChart,Month_number=Month_number)

    # User reached route via POST
    else:
        # Get all of the expenses provided from the HTML form
        formData = list(request.form.items())

        # Remove CSRF field from form data before processing
        formData.pop(0)

        # Add expenses to the DB for user
        expenses = e_expenses.addExpenses(formData, session["user_id"])

        # Redirect to results page and render a summary of the submitted expenses
        return render_template("expensed.html", results=expenses)


@app.route("/expenses", methods=["GET"])
@login_required
def expenses():
    """Manage expenses"""

    return render_template("expenses.html")


@app.route("/addexpenses", methods=["GET", "POST"])
@login_required
def addexpenses():
    """Add new expense(s)"""

    # User reached route via POST
    if request.method == "POST":
        # Get all of the expenses provided from the HTML form
        formData = list(request.form.items())

        # Remove CSRF field from form data before processing
        formData.pop(0)

        # Add expenses to the DB for user
        expenses = e_expenses.addExpenses(formData, session["user_id"])

        # Redirect to results page and render a summary of the submitted expenses
        return render_template("expensed.html", results=expenses)

    # User reached route via GET
    else:
        # Get the users spend categories
        categories = e_categories.getSpendCategories(session["user_id"])

        # Get the users payers
        payers = e_account.getPayers(session["user_id"])

        # Render expense page
        date = datetime.today().strftime('%Y-%m-%d')

        return render_template("addexpenses.html", categories=categories, date=date, payers=payers)


@app.route("/expensehistory", methods=["GET", "POST"])
@login_required
def expensehistory():
    """Show history of expenses or let the user update existing expense"""

    # User reached route via GET
    if request.method == "GET":
        # Get all of the users expense history ordered by submission time
        history = e_expenses.getHistory(session["user_id"])

        # Get the users spend categories
        categories = e_categories.getSpendCategories(session["user_id"])

        # Get the users payers (for modal)
        payers = e_account.getPayers(session["user_id"])

        return render_template("expensehistory.html", history=history, categories=categories, payers=payers, isDeleteAlert=False)

    # User reached route via POST
    else:
        # Initialize users action
        userHasSelected_deleteExpense = False

        # Determine what action was selected by the user (button/form trick from: https://stackoverflow.com/questions/26217779/how-to-get-the-name-of-a-submitted-form-in-flask)
        if "btnDeleteConfirm" in request.form:
            userHasSelected_deleteExpense = True
        elif "btnSave" in request.form:
            userHasSelected_deleteExpense = False
        else:
            return apology("Doh! Spend Categories is drunk. Try again!")

        # Get the existing expense record ID from the DB and build a data structure to store old expense details
        oldExpense = e_expenses.getExpense(
            request.form, session["user_id"])

        # Make sure an existing record was found otherwise render an error message
        if oldExpense["id"] == None:
            return apology("The expense record you're trying to update doesn't exist")

        # Delete the existing expense record
        if userHasSelected_deleteExpense == True:

            # Delete the old record from the DB
            deleted = e_expenses.deleteExpense(
                oldExpense, session["user_id"])
            if not deleted:
                return apology("The expense was unable to be deleted")

            # Get the users expense history, spend categories, payers, and then render the history page w/ delete alert
            history = e_expenses.getHistory(session["user_id"])
            categories = e_categories.getSpendCategories(
                session["user_id"])
            payers = e_account.getPayers(session["user_id"])
            return render_template("expensehistory.html", history=history, categories=categories, payers=payers, isDeleteAlert=True)

        # Update the existing expense record
        else:
            # Update the old record with new details from the form
            expensed = e_expenses.updateExpense(
                oldExpense, request.form, session["user_id"])
            if not expensed:
                return apology("The expense was unable to be updated")

            # Redirect to results page and render a summary of the updated expense
            return render_template("expensed.html", results=expensed)


@app.route("/budgets", methods=["GET", "POST"])
@app.route("/budgets/<int:year>", methods=["GET"])
@login_required
def budgets(year=None):
    """Manage budgets"""

    # Make sure the year from route is valid
    if year:
        currentYear = datetime.now().year
        if not 2020 <= year <= currentYear:
            return apology(f"Please select a valid budget year: 2020 through {currentYear}")
    else:
        # Set year to current year if it was not in the route (this will set UX to display current years budgets)
        year = datetime.now().year

    # User reached route via GET
    if request.method == "GET":
        # Get the users income
        income = e_account.getIncome(session["user_id"])

        # Get the users current budgets
        budgets = e_budgets.getBudgets(session["user_id"])

        # Get the users total budgeted amount
        budgeted = e_budgets.getTotalBudgetedByYear(
            session["user_id"], year)

        return render_template("budgets.html", income=income, budgets=budgets, year=year, budgeted=budgeted, deletedBudgetName=None)

    # User reached route via POST
    else:
        # Get the name of the budget the user wants to delete
        budgetName = request.form.get("delete").strip()

        # Delete the budget
        deletedBudgetName = e_budgets.deleteBudget(
            budgetName, session["user_id"])

        # Render the budgets page with a success message, otherwise throw an error/apology
        if deletedBudgetName:
            # Get the users income, current budgets, and sum their budgeted amount unless they don't have any budgets (same steps as a GET for this route)
            income = e_account.getIncome(session["user_id"])
            budgets = e_budgets.getBudgets(session["user_id"])
            budgeted = e_budgets.getTotalBudgetedByYear(
                session["user_id"], year)

            return render_template("budgets.html", income=income, budgets=budgets, year=year, budgeted=budgeted, deletedBudgetName=deletedBudgetName)
        else:
            return apology("Uh oh! Your budget could not be deleted.")


@app.route("/createbudget", methods=["GET", "POST"])
@login_required
def createbudget():
    """Create a budget"""

    # User reached route via POST
    if request.method == "POST":
        # Make sure user has no more than 20 budgets (note: 20 is an arbitrary value)
        budgets = e_budgets.getBudgets(session["user_id"])
        if budgets:
            budgetCount = 0
            for year in budgets:
                budgetCount += len(budgets[year])
            if budgetCount >= 20:
                return apology("You've reached the max amount of budgets'")

        # Get all of the budget info provided from the HTML form
        formData = list(request.form.items())

        # Remove CSRF field from form data before processing
        formData.pop(0)

        # Generate data structure to hold budget info from form
        budgetDict = e_budgets.generateBudgetFromForm(formData)

        # Render error message if budget name or categories contained invalid data
        if "apology" in budgetDict:
            return apology(budgetDict["apology"])
        else:
            # Add budget to DB for user
            budget = e_budgets.createBudget(
                budgetDict, session["user_id"])
            # Render error message if budget name is a duplicate of another budget the user has
            if "apology" in budget:
                return apology(budget["apology"])
            else:
                return render_template("budgetcreated.html", results=budget)
    else:
        # Get the users income
        income = e_account.getIncome(session["user_id"])

        # Get the users total budgeted amount
        budgeted = e_budgets.getTotalBudgetedByYear(session["user_id"])

        # Get the users spend categories
        categories = e_categories.getSpendCategories(session["user_id"])

        return render_template("createbudget.html", income=income, budgeted=budgeted, categories=categories)


@app.route("/updatebudget/<urlvar_budgetname>", methods=["GET", "POST"])
@login_required
def updatebudget(urlvar_budgetname):
    """Update a budget"""

    # User reached route via POST
    if request.method == "POST":
        # Get all of the budget info provided from the HTML form
        formData = list(request.form.items())

        # Remove CSRF field from form data before processing
        formData.pop(0)

        # Generate data structure to hold budget info from form
        budgetDict = e_budgets.generateBudgetFromForm(formData)

        # Render error message if budget name or categories contained invalid data
        if "apology" in budgetDict:
            return apology(budgetDict["apology"])
        else:
            # Update budget in the DB for user
            budget = e_budgets.updateBudget(
                urlvar_budgetname, budgetDict, session["user_id"])

            # Render error message if budget name is a duplicate of another budget the user has
            if "apology" in budget:
                return apology(budget["apology"])
            else:
                return render_template("budgetcreated.html", results=budget)

    # User reached route via GET
    else:
        # Get the budget details from the DB based on the budget name provided via URL. Throw an apology/error if budget can't be found.
        budgetID = e_budgets.getBudgetID(
            urlvar_budgetname, session["user_id"])
        if budgetID is None:
            return apology("'" + urlvar_budgetname + "' budget does not exist")
        else:
            budget = e_budgets.getBudgetByID(budgetID, session["user_id"])

        # Get the users income
        income = e_account.getIncome(session["user_id"])

        # Get the users total budgeted amount
        budgeted = e_budgets.getTotalBudgetedByYear(
            session["user_id"], budget['year'])

        # Generate the full, updatable budget data structure (name, amount for budget w/ all categories and their budgeted amounts)
        budget = e_budgets.getUpdatableBudget(budget, session["user_id"])

        # Render the budget update page
        return render_template("updatebudget.html", income=income, budgeted=budgeted, budget=budget)


@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    """Manage spending categories"""

    # User reached route via POST
    if request.method == "POST":

        # Initialize user's actions
        userHasSelected_newCategory = False
        userHasSelected_renameCategory = False
        userHasSelected_deleteCategory = False

        # Initialize user alerts
        alert_newCategory = None
        alert_renameCategory = None
        alert_deleteCategory = None

        # Determine what action was selected by the user (button/form trick from: https://stackoverflow.com/questions/26217779/how-to-get-the-name-of-a-submitted-form-in-flask)
        if "btnCreateCategory" in request.form:
            userHasSelected_newCategory = True
        elif "btnRenameCategory" in request.form:
            userHasSelected_renameCategory = True
        elif "btnDeleteCategory" in request.form:
            userHasSelected_deleteCategory = True
        else:
            return apology("Doh! Spend Categories is drunk. Try again!")

        # Get new category details and create a new record in the DB
        if userHasSelected_newCategory:

            # Get the new name provided by user
            newCategoryName = request.form.get("createName").strip()

            # Make sure user has no more than 30 categories (note: 30 is an arbitrary value)
            categoryCount = len(
                e_categories.getSpendCategories(session["user_id"]))
            if categoryCount >= 30:
                return apology("You've reached the max amount of categories")

            # Check to see if the new name already exists in the database (None == does not exist)
            categoryID = e_categories.getCategoryID(newCategoryName)

            # Category exists in the database already
            if categoryID:

                # Make sure the user isn't trying to add a category they already have by passing in the users ID now (None == does not exists)
                existingID = e_categories.getCategoryID(
                    newCategoryName, session["user_id"])
                if (existingID):
                    return apology("You already have '" + newCategoryName + "' category")
                # Add the category to the users account
                else:
                    e_categories.addCategory_User(
                        categoryID, session["user_id"])

            # Category does not exist in the DB already - create a new category and then add it to the users account
            else:
                # Creates a new category in the DB
                newCategoryID = e_categories.addCategory_DB(
                    newCategoryName)

                # Adds the category to the users account
                e_categories.addCategory_User(
                    newCategoryID, session["user_id"])

            # Set the alert message for user
            alert_newCategory = newCategoryName

        # Get renamed category details and update records in the DB
        if userHasSelected_renameCategory:

            # Get the new/old names provided by user
            oldCategoryName = request.form.get("oldname").strip()
            newCategoryName = request.form.get("newname").strip()

            # Check to see if the *old* category actually exists in the database (None == does not exist)
            oldCategoryID = e_categories.getCategoryID(oldCategoryName)

            # Old category does not exists in the database, throw error
            if oldCategoryID is None:
                return apology("The category you're trying to rename doesn't exist")

            # Check to see if the *new* name already exists in the database (None == does not exist)
            newCategoryID = e_categories.getCategoryID(newCategoryName)

            # Category exists in the database already
            if newCategoryID:

                # Make sure the user isn't trying to rename to a category they already have by passing in the users ID now (None == does not exists)
                existingID = e_categories.getCategoryID(
                    newCategoryName, session["user_id"])
                if existingID:
                    return apology("You already have '" + newCategoryName + "' category")

                # Get the new category name from the DB (prevents string upper/lowercase inconsistencies that can result from using the users input from the form instead of the DB)
                newCategoryNameFromDB = e_categories.getSpendCategoryName(
                    newCategoryID)

                # Rename the category
                e_categories.renameCategory(
                    oldCategoryID, newCategoryID, oldCategoryName, newCategoryNameFromDB, session["user_id"])

            # Category does not exist in the DB already - create a new category and then add it to the users account
            else:
                # Creates a new category in the DB
                newCategoryID = e_categories.addCategory_DB(
                    newCategoryName)

                # Rename the category
                e_categories.renameCategory(
                    oldCategoryID, newCategoryID, oldCategoryName, newCategoryName, session["user_id"])

            # Set the alert message for user
            alert_renameCategory = [oldCategoryName, newCategoryName]

        # Get deleted category details and update records in the DB
        if userHasSelected_deleteCategory:

            # Get the name of the category the user wants to delete
            deleteName = request.form.get("delete").strip()

            # Check to see if the category actually exists in the database (None == does not exist)
            categoryID = e_categories.getCategoryID(deleteName)

            # Category does not exists in the database, throw error
            if categoryID is None:
                return apology("The category you're trying to delete doesn't exist")

            # Make sure user has at least 1 category (do not allow 0 categories)
            categoryCount = len(
                e_categories.getSpendCategories(session["user_id"]))
            if categoryCount <= 1:
                return apology("You need to keep at least 1 spend category")

            # Delete the category
            e_categories.deleteCategory(categoryID, session["user_id"])

            # Set the alert message for user
            alert_deleteCategory = deleteName

        # Get the users spend categories
        categories = e_categories.getSpendCategories(session["user_id"])

        return render_template("categories.html", categories=categories, newCategory=alert_newCategory, renamedCategory=alert_renameCategory, deleteCategory=alert_deleteCategory)

    # User reached route via GET
    else:
        # Get the users spend categories
        categories = e_categories.getSpendCategories(session["user_id"])

        # Get the budgets associated with each spend category
        categoryBudgets = e_categories.getBudgetsSpendCategories(
            session["user_id"])

        # Generate a single data structure for storing all categories and their associated budgets
        categoriesWithBudgets = e_categories.generateSpendCategoriesWithBudgets(
            categories, categoryBudgets)

        return render_template("categories.html", categories=categoriesWithBudgets, newCategory=None, renamedCategory=None, deleteCategory=None)


@app.route("/reports", methods=["GET"])
@login_required
def reports():
    """View reports"""

    return render_template("reports.html")


@app.route("/budgetsreport", methods=["GET"])
@app.route("/budgetsreport/<int:year>", methods=["GET"])
@login_required
def budgetsreport(year=None):
    """View year-to-date spending by category report"""

    # Make sure the year from route is valid
    if year:
        currentYear = datetime.now().year
        if not 2020 <= year <= currentYear:
            return apology(f"Please select a valid budget year: 2020 through {currentYear}")
    else:
        # Set year to current year if it was not in the route (this will set UX to display current years budgets)
        year = datetime.now().year

    # Generate a data structure that combines the users budgets and the expenses that have categories which match budgets
    budgets = tendie_reports.generateBudgetsReport(session["user_id"], year)

    return render_template("budgetsreport.html", budgets=budgets, year=year)


@app.route("/monthlyreport", methods=["GET"])
@app.route("/monthlyreport/<int:year>", methods=["GET"])
@login_required
def monthlyreport(year=None):
    """View monthly spending report"""

    # Make sure the year from route is valid
    if year:
        currentYear = datetime.now().year
        if not 2020 <= year <= currentYear:
            return apology(f"Please select a valid budget year: 2020 through {currentYear}")
    else:
        # Set year to current year if it was not in the route (this will set UX to display current years report)
        year = datetime.now().year

    # Generate a data structure that combines the users monthly spending data needed for chart and table
    monthlySpending = tendie_reports.generateMonthlyReport(
        session["user_id"], year)

    return render_template("monthlyreport.html", monthlySpending=monthlySpending, year=year)


@app.route("/spendingreport", methods=["GET"])
@app.route("/spendingreport/<int:year>", methods=["GET"])
@login_required
def spendingreport(year=None):
    """View spending categories report"""

    # Make sure the year from route is valid
    if year:
        currentYear = datetime.now().year
        if not 2020 <= year <= currentYear:
            return apology(f"Please select a valid budget year: 2020 through {currentYear}")
    else:
        # Set year to current year if it was not in the route (this will set UX to display current years report)
        year = datetime.now().year

    # Generate a data structure that combines the users all-time spending data for chart and table
    spendingReport = tendie_reports.generateSpendingTrendsReport(
        session["user_id"], year)

    return render_template("spendingreport.html", spending_trends_chart=spendingReport["chart"], spending_trends_table=spendingReport["table"], categories=spendingReport["categories"], year=year)


@app.route("/payersreport", methods=["GET"])
@app.route("/payersreport/<int:year>", methods=["GET"])
@login_required
def payersreport(year=None):
    """View payers spending report"""

    # Make sure the year from route is valid
    if year:
        currentYear = datetime.now().year
        if not 2020 <= year <= currentYear:
            return apology(f"Please select a valid budget year: 2020 through {currentYear}")
    else:
        # Set year to current year if it was not in the route (this will set UX to display current years report)
        year = datetime.now().year

    # Generate a data structure that combines the users payers and expense data for chart and table
    payersReport = tendie_reports.generatePayersReport(
        session["user_id"], year)

    return render_template("payersreport.html", payers=payersReport, year=year)

# Route to fetch notification preferences for a user
@app.route("/analytics", methods=["GET", "POST"])
@login_required  # Assuming you have a login_required decorator for route protection
def get_notification_preferences():
        """FOR ANALYTICS"""
        if request.method == 'GET':
            id = session["user_id"]
            #monthyear = tendie_account.getUserdate(session["user_id"])
            monthyear = request.args.get("month")
            savings_goal_percentage = float(request.args.get('goal',2)) 

            income = e_account.getIncome(session["user_id"])

            #defined_value = [{"percent": 5}, {"percent": 10},{"percent": 15}, {"percent": 20},{"percent": 25}, {"percent": 30}] 

            savings_target = ( savings_goal_percentage / 100) * income

            monthlist = e_analytics.getSpenddateyear(session["user_id"])   
            saved_amount = db.execute("select  (u.income - COALESCE(sum(amount),0)) ::int as saved_amount from public.users u , public.expenses  e where e.user_id = u.id and user_id = :idd and to_char(expensedate::date, 'YYYY-MM') = :month and category not in ('Investment') group by u.income",
                                     {"month": monthyear,"idd": id} ).fetchone()
            if saved_amount is not None:
                saved_amount = saved_amount[0]
            else:
                saved_amount = 0
            
            expenses = db.execute("select user_id,category,amount, to_char(expensedate::date, 'YYYY-MM') as monthyear from public.expenses where user_id = :idd and  to_char(expensedate::date, 'YYYY-MM') = :month order by monthyear desc",
                                {"month": monthyear,"idd": id}).fetchall()

            total_expenses = sum(expense.amount for expense in expenses)

            monthly_expenditure = income - saved_amount

            # Analyze spending patterns and identify categories where the user spends the most money
            category_expenses = {}
            for expense in expenses:
                category = expense.category
                category_expenses[category] = category_expenses.get(category, 0) + expense.amount

            # Sort categories by total expenses
            sorted_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)

            recommendations = []
            counter = []
            if saved_amount >= savings_target:
                recommendations.append("Congratulations! You have reached your savings target.")
                counter.append(1)
            else:
                recommendations.append(f"You need to save Rs {savings_target - saved_amount:.2f} more to reach your target.")
                counter.append(0)

            # Rule-based additional savings strategies
            if monthly_expenditure > (income * 0.7):
                recommendations.append("Consider reducing discretionary spending.")
                counter.append(1)
            elif monthly_expenditure > (income * 0.6):
                recommendations.append("Optimize recurring expenses to save more.")
                counter.append(2)
            else:
                recommendations.append("Keep up the good work on managing your expenses.")
                counter.append(0)

            if saved_amount > (income * 0.22):
                recommendations.append("Congratulations! Your monthly holdings goal is achieved")
                counter.append(1)
            else:
                recommendations.append(f"You need to invest or save Rs {income * 0.22:.2f} to reach your target.")
                counter.append(0)

            first = recommendations
            count1 = counter
            
            return render_template("notification.html",sortcat =sorted_categories,saved_amount = saved_amount,
                                savings_target=savings_target,total_expenses=total_expenses,monthlist=monthlist,svgope=savings_goal_percentage,
                                first = first,count1 = count1)

        elif request.method =='POST':
            pass
            

@app.route("/account", methods=["GET", "POST"])
@login_required
def updateaccount():
    """Update users account"""

    # User reached route via POST
    if request.method == "POST":

        # Initialize user's actions
        userHasSelected_updateIncome = False
        userHasSelected_addPayer = False
        userHasSelected_renamePayer = False
        userHasSelected_deletePayer = False
        userHasSelected_updatePassword = False

        # Initialize user alerts
        alert_updateIncome = None
        alert_addPayer = None
        alert_renamePayer = None
        alert_deletePayer = None
        alert_updatePassword = None

        # Determine what action was selected by the user (button/form trick from: https://stackoverflow.com/questions/26217779/how-to-get-the-name-of-a-submitted-form-in-flask)
        if "btnUpdateIncome" in request.form:
            userHasSelected_updateIncome = True
        elif "btnSavePayer" in request.form:
            userHasSelected_addPayer = True
        elif "btnRenamePayer" in request.form:
            userHasSelected_renamePayer = True
        elif "btnDeletePayer" in request.form:
            userHasSelected_deletePayer = True
        elif "btnUpdatePassword" in request.form:
            userHasSelected_updatePassword = True
        else:
            return apology("Doh! Your Account is drunk. Try again!")

        # TODO make sure user can't have more than X payers total (like categories, budgets, etc.)

        # Get new income details and update record in the DB
        if userHasSelected_updateIncome:

            # Get the new income amount
            newIncome = float(request.form.get("income").strip())

            # Update the users income
            updatedIncome = e_account.updateIncome(
                newIncome, session["user_id"])

            # Render error message if the users income record could not be updated
            if updatedIncome != 1:
                return apology(updatedIncome["apology"])

            # Set the alert message for user
            alert_updateIncome = newIncome

        # Get new payer details and update record in the DB
        if userHasSelected_addPayer:

            # Get the new payers name from form
            newName = request.form.get("payerName").strip()

            # Add the payer
            newPayer = e_account.addPayer(newName, session["user_id"])

            # Render error message if payer name is a duplicate of another payer the user has
            if newPayer != 1:
                return apology(newPayer["apology"])

            # Set the alert message for user
            alert_addPayer = newName

        if userHasSelected_renamePayer:

            # Get the old and new payer names from form
            oldName = request.form.get("oldpayer").strip()
            newName = request.form.get("newpayer").strip()

            # Rename the payer
            renamedPayer = e_account.renamePayer(
                oldName, newName, session["user_id"])

            # Render error message if payer name is a duplicate of another payer the user has
            if renamedPayer != 1:
                return apology(renamedPayer["apology"])

            # Set the alert message for user
            alert_renamePayer = [oldName, newName]

        if userHasSelected_deletePayer:

            # Get the payer name from form
            name = request.form.get("delete").strip()

            # Delete the payer
            deletedPayer = e_account.deletePayer(name, session["user_id"])

            # Render error message if the name could not be deleted
            if deletedPayer != 1:
                return apology(renamedPayer["apology"])

            # Set the alert message for user
            alert_deletePayer = name

        if userHasSelected_updatePassword:

            # Try updating the users password
            updatedPassword = e_account.updatePassword(request.form.get(
                "currentPassword"), request.form.get("newPassword"), session["user_id"])

            # Render error message if the password could not be updated
            if updatedPassword != 1:
                return apology(updatedPassword["apology"])

            # Set the alert message for user
            alert_updatePassword = True

        # Get the users account name, income, payers, and stats
        user = e_account.getAllUserInfo(session["user_id"])

        return render_template("account.html", username=user["name"], income=user["income"], payers=user["payers"], stats=user["stats"], newIncome=alert_updateIncome, addPayer=alert_addPayer, renamedPayer=alert_renamePayer, deletedPayer=alert_deletePayer, updatedPassword=alert_updatePassword)
    else:

        # Get the users account name, income, payers, and stats
        user = e_account.getAllUserInfo(session["user_id"])

        return render_template("account.html", username=user["name"], income=user["income"], payers=user["payers"], stats=user["stats"], newIncome=None, addPayer=None, renamedPayer=None, deletedPayer=None, updatedPassword=None)


# Handle errors by rendering apology
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run(port=5001)
    # run() method of Flask class runs the application
    # on the local development server.
    app.run()