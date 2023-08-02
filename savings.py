from flask import Flask, render_template

app = Flask(__name__)

# Dummy expense data for demonstration
expense_data = [
    {'category': 'Groceries', 'amount': 300},
    {'category': 'Utilities', 'amount': 150},
    {'category': 'Dining Out', 'amount': 200},
    {'category': 'Shopping', 'amount': 100},
    {'category': 'Rent', 'amount': 800},
]

# Set financial goals (as a percentage of income)
savings_goal_percentage = 20

# Calculate total monthly income (dummy value)
monthly_income = 3000


@app.route('/')
def home():
    total_expenses = sum(expense['amount'] for expense in expense_data)
    savings_target = (savings_goal_percentage / 100) * monthly_income
    savings_gap = savings_target - total_expenses
    savings_recommendations = generate_savings_recommendations(total_expenses, savings_target)

    return render_template('savings.html', total_expenses=total_expenses, savings_target=savings_target,
                           savings_gap=savings_gap, savings_recommendations=savings_recommendations)


def generate_savings_recommendations(total_expenses, savings_target):
    # Rule-based savings recommendations based on savings gap
    recommendations = []
    if total_expenses >= savings_target:
        recommendations.append("Congratulations! You have reached your savings target.")
    else:
        recommendations.append(f"You need to save ${savings_target - total_expenses:.2f} more to reach your target.")

    # Rule-based additional savings strategies
    if total_expenses > (monthly_income * 0.6):
        recommendations.append("Consider reducing discretionary spending.")
    elif total_expenses > (monthly_income * 0.5):
        recommendations.append("Optimize recurring expenses to save more.")
    else:
        recommendations.append("Keep up the good work on managing your expenses.")

    return recommendations


if __name__ == '__main__':
    app.run(debug=True)
