"""Financial calculators for mortgage and EMI computations."""
import math
from typing import List


def compute_emi(principal: float, annual_rate: float, years: int) -> dict:
    """
    Calculate EMI using standard formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    Returns monthly EMI, total payment, and total interest.
    """
    if annual_rate <= 0:
        monthly = principal / (years * 12)
        return {
            "monthly_emi": round(monthly, 2),
            "total_payment": round(principal, 2),
            "total_interest": 0.0,
            "principal": round(principal, 2),
        }
    r = annual_rate / 100 / 12
    n = years * 12
    emi = principal * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
    total = emi * n
    return {
        "monthly_emi": round(emi, 2),
        "total_payment": round(total, 2),
        "total_interest": round(total - principal, 2),
        "principal": round(principal, 2),
    }


def amortization_schedule(principal: float, annual_rate: float, years: int) -> List[dict]:
    """Generate month-by-month amortization schedule."""
    if annual_rate <= 0:
        return []
    r = annual_rate / 100 / 12
    n = years * 12
    emi = principal * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
    balance = principal
    schedule = []
    for month in range(1, n + 1):
        interest = balance * r
        principal_part = emi - interest
        balance -= principal_part
        schedule.append({
            "month": month,
            "emi": round(emi, 2),
            "principal": round(principal_part, 2),
            "interest": round(interest, 2),
            "balance": round(max(balance, 0), 2),
        })
    return schedule


def mortgage_estimate(price: float, down_pct: float, years: int, rate: float) -> dict:
    """Full mortgage estimate including loan amount and EMI breakdown."""
    down = price * down_pct / 100
    loan = price - down
    emi_data = compute_emi(loan, rate, years)
    return {
        "property_price": round(price, 2),
        "down_payment": round(down, 2),
        "loan_amount": round(loan, 2),
        "down_payment_percent": down_pct,
        **emi_data,
    }
