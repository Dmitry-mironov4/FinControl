import math

def savings_rate(income, expense):
    if income == 0:
        return 0.0
    return (income - expense) / income * 100.0

def moving_average(values, n):
    if not values:
        return 0.0
    window = values[-n:] if len(values) >= n else values
    return sum(window) / len(window)

def linear_forecast(values, steps):
    n = len(values)
    if n < 2:
        return None
    x = list(range(n))
    y = values
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    b = numerator / denominator if denominator != 0 else 0.0
    a = y_mean - b * x_mean
    forecast = [a + b * (n + i) for i in range(steps)]
    return forecast

def goal_analysis(target, current, monthly_savings):
    if current >= target:
        return 0
    if monthly_savings <= 0:
        return None
    return math.ceil((target - current) / monthly_savings)

def subscription_load(subscriptions_total, income):
    if income == 0:
        return 0.0
    return (subscriptions_total / income) * 100.0