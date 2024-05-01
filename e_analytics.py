import os
import calendar

from flask import request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
from helpers import convertSQLToDict

# Create engine object to manage connections to DB, and scoped session to separate user interactions with DB
engine = create_engine("postgres://postgres:Winston()@localhost:5432/postgres")
db = scoped_session(sessionmaker(bind=engine))

# Gets and return the users spend categories
def getSpenddateyear(userID):
    results = db.execute(
        "select distinct to_char(expensedate::date, 'YYYY-MM') as monthyear from public.expenses where user_id = :usersID order by 1 desc",
        {"usersID": userID}).fetchall()

    name = convertSQLToDict(results)

    return name
# 
# def analyze_expenses(monthyear,userID):
#     # Query the database to retrieve monthly expense data for the specified month and year
#     expenses = db.execute("with cte as(select user_id,category,amount, to_char(expensedate::date, 'YYYY-MM') as monthyear from public.expenses where user_id = :usersID )select * from cte where monthyear = :month order by monthyear desc",
#                             {"month": monthyear,"usersID": userID}).fetchall()

#     total_expenses = sum(expense.amount for expense in expenses)

#     # Analyze spending patterns and identify categories where the user spends the most money
#     category_expenses = {}
#     for expense in expenses:
#         category = expense.category
#         category_expenses[category] = category_expenses.get(category, 0) + expense.amount

#     # Sort categories by total expenses
#     sorted_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)

#     return total_expenses, sorted_categories

# def suggest_savings(total_expenses, sorted_categories, savings_goal):
#     savings_suggestions = []

#     # Calculate the difference between total expenses and savings goal
#     savings_needed = savings_goal - total_expenses

#     if savings_needed > 0:
#         savings_suggestions.append("You need to save ${:.2f} more this month to reach your savings goal.".format(savings_needed))
#     else:
#         savings_suggestions.append("Congratulations! You've reached your savings goal for this month.")

#     # Provide suggestions based on spending patterns
#     if sorted_categories:
#         top_category, top_category_expense = sorted_categories[0]
#         savings_suggestions.append("You spent the most on {} this month. Consider reducing expenses in this category.".format(top_category))

#     return savings_suggestions

# # Example usage:
# month = 7
# year = 2023
# savings_goal = 1000

# total_expenses, sorted_categories = analyze_expenses(month, year)
# savings_suggestions = suggest_savings(total_expenses, sorted_categories, savings_goal)

# for suggestion in savings_suggestions:
#     print(suggestion)

# ## second step
# # Dummy expense data for demonstration
# expense_data = [
#     {'category': 'Groceries', 'amount': 300},
#     {'category': 'Utilities', 'amount': 150},
#     {'category': 'Dining Out', 'amount': 200},
#     {'category': 'Shopping', 'amount': 100},
#     {'category': 'Rent', 'amount': 800},
# ]

# # Set financial goals (as a percentage of income)
# savings_goal_percentage = 20

# # Calculate total monthly income (dummy value)
# monthly_income = 3000








# def home():
#     total_expenses = sum(expense['amount'] for expense in expense_data)
#     savings_target = (savings_goal_percentage / 100) * monthly_income
#     savings_gap = savings_target - total_expenses
#     savings_recommendations = generate_savings_recommendations(total_expenses, savings_target)
#     return savings_gap, savings_recommendations


# def generate_savings_recommendations(total_expenses, savings_target):
#     # Rule-based savings recommendations based on savings gap
#     recommendations = []
#     if total_expenses >= savings_target:
#         recommendations.append("Congratulations! You have reached your savings target.")
#     else:
#         recommendations.append(f"You need to save ${savings_target - total_expenses:.2f} more to reach your target.")

#     # Rule-based additional savings strategies
#     if total_expenses > (monthly_income * 0.6):
#         recommendations.append("Consider reducing discretionary spending.")
#     elif total_expenses > (monthly_income * 0.5):
#         recommendations.append("Optimize recurring expenses to save more.")
#     else:
#         recommendations.append("Keep up the good work on managing your expenses.")

#     return recommendations

