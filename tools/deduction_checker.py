"""
Deduction Checker Tool - FY 2025-26
Checks all deductions a salaried person is eligible for,
how much they have used, and how much room is left.

Only relevant for OLD regime. New regime does not allow these deductions.

Author: Tax Intelligence System
Verified by: CA [Your Sister's Name]
"""

from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class UserProfile:
    """
    Complete profile of a salaried user.
    This is what the Profile Agent builds and maintains.
    All amounts in INR.
    """

    # Basic info
    name: str
    age: int
    city: str                          # Metro or non-metro matters for HRA
    is_metro: bool = False             # Mumbai, Delhi, Kolkata, Chennai = metro

    # Salary details
    gross_salary: float = 0
    basic_salary: float = 0            # Usually 40-50% of CTC
    hra_received: float = 0            # HRA component in salary
    rent_paid_monthly: float = 0       # Actual rent paid per month

    # 80C investments (limit: 1,50,000 total)
    epf_contribution: float = 0        # Employee PF contribution
    ppf_contribution: float = 0
    elss_investment: float = 0
    life_insurance_premium: float = 0
    home_loan_principal: float = 0     # Principal repayment under 80C
    nsc_investment: float = 0
    tuition_fees: float = 0            # Children tuition fees max 2 kids
    sukanya_samriddhi: float = 0
    tax_saving_fd: float = 0           # 5 year tax saving FD

    # 80D health insurance (limit varies)
    self_health_insurance: float = 0   # Self + spouse + children
    parent_health_insurance: float = 0 # Parents premium
    are_parents_senior_citizen: bool = False  # Above 60 = senior citizen

    # 80CCD1B NPS (limit: 50,000 over and above 80C)
    nps_contribution: float = 0

    # 80E education loan
    education_loan_interest: float = 0  # No limit, entire interest deductible

    # 80G donations
    donations_50_percent: float = 0    # 50% deductible donations
    donations_100_percent: float = 0   # 100% deductible donations

    # 80TTA savings interest (limit: 10,000)
    savings_account_interest: float = 0

    # 24B home loan interest (limit: 2,00,000)
    home_loan_interest: float = 0
    has_home_loan: bool = False

    # Other
    tds_deducted: float = 0
    other_income: float = 0


@dataclass
class DeductionItem:
    """Represents a single deduction with its status."""
    section: str           # e.g. "80C"
    name: str              # e.g. "PPF Investment"
    max_limit: float       # Maximum allowed by law
    utilized: float        # What user has already done
    remaining: float       # How much more they can do
    is_eligible: bool      # Is user eligible for this deduction
    message: str           # Human readable message for the agent
    is_missed: bool = False  # True if user is eligible but not using it


@dataclass
class DeductionReport:
    """Complete deduction report for a user profile."""
    user_name: str
    total_possible_deductions: float
    total_utilized_deductions: float
    total_remaining_deductions: float
    potential_tax_saving: float        # Rough saving at their slab rate
    items: list = field(default_factory=list)
    missed_opportunities: list = field(default_factory=list)
    alerts: list = field(default_factory=list)


# ─────────────────────────────────────────────
# HRA CALCULATION
# ─────────────────────────────────────────────

def calculate_hra_exemption(profile: UserProfile) -> float:
    """
    HRA exemption is minimum of three:
    1. Actual HRA received from employer
    2. Rent paid - 10% of basic salary
    3. 50% of basic (metro) or 40% of basic (non-metro)

    Metro cities: Mumbai, Delhi, Kolkata, Chennai
    """
    if profile.rent_paid_monthly == 0 or profile.hra_received == 0:
        return 0

    annual_rent = profile.rent_paid_monthly * 12
    basic = profile.basic_salary

    condition_1 = profile.hra_received
    condition_2 = annual_rent - (0.10 * basic)
    condition_3 = 0.50 * basic if profile.is_metro else 0.40 * basic

    exemption = min(condition_1, condition_2, condition_3)
    return max(0, exemption)  # Cannot be negative


# ─────────────────────────────────────────────
# MAIN TOOL FUNCTION
# ─────────────────────────────────────────────

def check_deductions(profile: UserProfile) -> DeductionReport:
    """
    Main deduction checker function.
    Goes through every deduction, checks eligibility,
    calculates utilized and remaining amounts.
    """

    items = []
    missed_opportunities = []
    alerts = []

    # ── 1. STANDARD DEDUCTION ──
    std_deduction = min(profile.gross_salary, 50000)
    items.append(DeductionItem(
        section="Standard Deduction",
        name="Standard Deduction (Automatic)",
        max_limit=50000,
        utilized=std_deduction,
        remaining=0,
        is_eligible=True,
        message="Automatically applied. No action needed.",
        is_missed=False
    ))

    # ── 2. HRA EXEMPTION ──
    hra_exemption = calculate_hra_exemption(profile)
    hra_missed = profile.rent_paid_monthly > 0 and profile.hra_received == 0
    hra_not_claiming = profile.hra_received > 0 and profile.rent_paid_monthly == 0

    hra_message = ""
    if hra_exemption > 0:
        hra_message = f"HRA exemption of ₹{hra_exemption:,.0f} applicable. Submit rent receipts to employer."
    elif hra_missed:
        hra_message = "You pay rent but HRA is not in your salary structure. Negotiate with employer to restructure CTC."
        missed_opportunities.append("HRA exemption — restructure salary to include HRA component")
    elif hra_not_claiming:
        hra_message = "You receive HRA but are not paying rent. No exemption applicable."
    else:
        hra_message = "No HRA in salary or not paying rent."

    items.append(DeductionItem(
        section="HRA",
        name="House Rent Allowance Exemption",
        max_limit=profile.hra_received,
        utilized=hra_exemption,
        remaining=profile.hra_received - hra_exemption,
        is_eligible=profile.hra_received > 0 and profile.rent_paid_monthly > 0,
        message=hra_message,
        is_missed=hra_missed
    ))

    # ── 3. SECTION 80C (Limit: 1,50,000) ──
    total_80c = (
        profile.epf_contribution +
        profile.ppf_contribution +
        profile.elss_investment +
        profile.life_insurance_premium +
        profile.home_loan_principal +
        profile.nsc_investment +
        profile.tuition_fees +
        profile.sukanya_samriddhi +
        profile.tax_saving_fd
    )
    utilized_80c = min(total_80c, 150000)
    remaining_80c = max(0, 150000 - total_80c)

    if remaining_80c > 0:
        alerts.append(f"80C: ₹{remaining_80c:,.0f} limit unused. Invest in ELSS, PPF, or top up EPF voluntarily to save more tax.")

    items.append(DeductionItem(
        section="80C",
        name="Tax Saving Investments (ELSS, PPF, EPF, LIC etc.)",
        max_limit=150000,
        utilized=utilized_80c,
        remaining=remaining_80c,
        is_eligible=True,
        message=f"Used ₹{utilized_80c:,.0f} of ₹1,50,000 limit. ₹{remaining_80c:,.0f} remaining.",
        is_missed=total_80c == 0
    ))

    # ── 4. SECTION 80D (Health Insurance) ──
    # Self + family: max 25,000 (non-senior) 
    # Parents: max 25,000 (non-senior) or 50,000 (senior citizen)
    self_80d_limit = 25000
    parent_80d_limit = 50000 if profile.are_parents_senior_citizen else 25000

    utilized_80d_self = min(profile.self_health_insurance, self_80d_limit)
    utilized_80d_parent = min(profile.parent_health_insurance, parent_80d_limit)
    total_utilized_80d = utilized_80d_self + utilized_80d_parent
    total_80d_limit = self_80d_limit + parent_80d_limit
    remaining_80d = total_80d_limit - total_utilized_80d

    if profile.self_health_insurance == 0:
        missed_opportunities.append(f"80D: No self health insurance. Buy a policy to claim up to ₹25,000 deduction.")

    if profile.parent_health_insurance == 0:
        parent_limit_str = "₹50,000" if profile.are_parents_senior_citizen else "₹25,000"
        missed_opportunities.append(f"80D: No parent health insurance. Buy a policy to claim up to {parent_limit_str} deduction.")

    items.append(DeductionItem(
        section="80D",
        name="Health Insurance Premium",
        max_limit=total_80d_limit,
        utilized=total_utilized_80d,
        remaining=remaining_80d,
        is_eligible=True,
        message=f"Self/family limit: ₹25,000. Parent limit: ₹{parent_80d_limit:,.0f}. Used: ₹{total_utilized_80d:,.0f}. Remaining: ₹{remaining_80d:,.0f}.",
        is_missed=total_utilized_80d == 0
    ))

    # ── 5. SECTION 80CCD1B (NPS extra deduction: limit 50,000) ──
    utilized_nps = min(profile.nps_contribution, 50000)
    remaining_nps = max(0, 50000 - profile.nps_contribution)

    if profile.nps_contribution == 0:
        missed_opportunities.append("80CCD1B: No NPS investment. Invest up to ₹50,000 for additional deduction OVER AND ABOVE 80C limit.")

    items.append(DeductionItem(
        section="80CCD1B",
        name="NPS (National Pension Scheme) - Extra Deduction",
        max_limit=50000,
        utilized=utilized_nps,
        remaining=remaining_nps,
        is_eligible=True,
        message=f"This is SEPARATE from 80C. Additional ₹50,000 deduction available. Used: ₹{utilized_nps:,.0f}. Remaining: ₹{remaining_nps:,.0f}.",
        is_missed=profile.nps_contribution == 0
    ))

    # ── 6. SECTION 80E (Education Loan Interest) ──
    if profile.education_loan_interest > 0:
        items.append(DeductionItem(
            section="80E",
            name="Education Loan Interest",
            max_limit=profile.education_loan_interest,  # No upper limit
            utilized=profile.education_loan_interest,
            remaining=0,
            is_eligible=True,
            message=f"Full interest of ₹{profile.education_loan_interest:,.0f} deductible. No upper limit. Available for 8 years.",
            is_missed=False
        ))

    # ── 7. SECTION 80G (Donations) ──
    total_donations = profile.donations_100_percent + (profile.donations_50_percent * 0.5)
    if total_donations > 0:
        items.append(DeductionItem(
            section="80G",
            name="Donations to Charitable Institutions",
            max_limit=total_donations,
            utilized=total_donations,
            remaining=0,
            is_eligible=True,
            message=f"Deductible donation amount: ₹{total_donations:,.0f}. Keep receipts and 80G certificates.",
            is_missed=False
        ))

    # ── 8. SECTION 80TTA / 80TTB (Interest on Deposits) ──
    if profile.age >= 60:
        # Senior Citizen Section 80TTB limit: 50,000 (applies to savings and FD/other deposit interest)
        interest_income = profile.savings_account_interest + profile.other_income
        utilized_80ttb = min(interest_income, 50000)
        items.append(DeductionItem(
            section="80TTB",
            name="Interest on Deposits for Senior Citizens (Savings/FD)",
            max_limit=50000,
            utilized=utilized_80ttb,
            remaining=max(0.0, 50000 - interest_income),
            is_eligible=True,
            message=f"Senior citizen interest deduction u/s 80TTB (Savings/FD) up to ₹50,000. Utilized: ₹{utilized_80ttb:,.0f}. Remaining: ₹{max(0.0, 50000 - interest_income):,.0f}.",
            is_missed=interest_income == 0
        ))
    else:
        # Non-Senior Section 80TTA limit: 10,000 (applies to savings account interest only)
        utilized_80tta = min(profile.savings_account_interest, 10000)
        items.append(DeductionItem(
            section="80TTA",
            name="Savings Account Interest",
            max_limit=10000,
            utilized=utilized_80tta,
            remaining=max(0.0, 10000 - profile.savings_account_interest),
            is_eligible=True,
            message=f"Savings interest up to ₹10,000 is exempt. Your interest: ₹{profile.savings_account_interest:,.0f}. Exempt: ₹{utilized_80tta:,.0f}.",
            is_missed=profile.savings_account_interest == 0
        ))

    # ── 9. SECTION 24B (Home Loan Interest: limit 2,00,000) ──
    if profile.has_home_loan:
        utilized_24b = min(profile.home_loan_interest, 200000)
        remaining_24b = max(0, 200000 - profile.home_loan_interest)
        items.append(DeductionItem(
            section="24B",
            name="Home Loan Interest",
            max_limit=200000,
            utilized=utilized_24b,
            remaining=remaining_24b,
            is_eligible=True,
            message=f"Home loan interest deduction up to ₹2,00,000. Used: ₹{utilized_24b:,.0f}.",
            is_missed=False
        ))

    # ── CALCULATE TOTALS ──
    total_possible = sum(item.max_limit for item in items)
    total_utilized = sum(item.utilized for item in items)
    total_remaining = sum(item.remaining for item in items if item.remaining > 0)

    # Rough tax saving estimate at 30% slab (conservative upper estimate)
    # In reality depends on their actual slab
    potential_saving = total_remaining * 0.30

    return DeductionReport(
        user_name=profile.name,
        total_possible_deductions=total_possible,
        total_utilized_deductions=total_utilized,
        total_remaining_deductions=total_remaining,
        potential_tax_saving=potential_saving,
        items=items,
        missed_opportunities=missed_opportunities,
        alerts=alerts
    )


# ─────────────────────────────────────────────
# PRETTY PRINT HELPER
# ─────────────────────────────────────────────

def print_deduction_report(report: DeductionReport):
    """Print a clean readable deduction report."""
    print(f"\n{'='*55}")
    print(f"  DEDUCTION REPORT FOR: {report.user_name}")
    print(f"  FY 2025-26 | Old Regime")
    print(f"{'='*55}")
    print(f"  Total Deductions Possible  : ₹{report.total_possible_deductions:,.0f}")
    print(f"  Total Utilized             : ₹{report.total_utilized_deductions:,.0f}")
    print(f"  Total Remaining            : ₹{report.total_remaining_deductions:,.0f}")
    print(f"  Potential Tax Saving Left  : ₹{report.potential_tax_saving:,.0f} (approx)")

    print(f"\n  DEDUCTION BREAKDOWN:")
    print(f"  {'-'*50}")
    for item in report.items:
        status = "✅" if item.utilized > 0 else "❌"
        print(f"\n  {status} {item.section} — {item.name}")
        print(f"     Limit    : ₹{item.max_limit:,.0f}")
        print(f"     Utilized : ₹{item.utilized:,.0f}")
        if item.remaining > 0:
            print(f"     Remaining: ₹{item.remaining:,.0f} ← ACTION NEEDED")
        print(f"     Note     : {item.message}")

    if report.missed_opportunities:
        print(f"\n  🚨 MISSED OPPORTUNITIES:")
        for i, opp in enumerate(report.missed_opportunities, 1):
            print(f"     {i}. {opp}")

    if report.alerts:
        print(f"\n  ⚠️  ALERTS:")
        for alert in report.alerts:
            print(f"     → {alert}")

    print(f"\n{'='*55}\n")


# ─────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n📋 DEDUCTION CHECKER - FY 2025-26\n")

    # ── TEST CASE 1: Rahul — missing many deductions ──
    rahul = UserProfile(
        name="Rahul",
        age=26,
        city="Chennai",
        is_metro=True,
        gross_salary=1200000,
        basic_salary=480000,        # 40% of CTC
        hra_received=240000,        # 20% of CTC
        rent_paid_monthly=15000,
        epf_contribution=57600,     # 12% of basic
        ppf_contribution=50000,
        # No health insurance
        # No NPS
        # No parent health insurance
        savings_account_interest=5000,
        tds_deducted=50000
    )
    rahul_report = check_deductions(rahul)
    print_deduction_report(rahul_report)

    # ── TEST CASE 2: Amit — fully optimized ──
    amit = UserProfile(
        name="Amit",
        age=35,
        city="Mumbai",
        is_metro=True,
        gross_salary=1800000,
        basic_salary=720000,
        hra_received=360000,
        rent_paid_monthly=30000,
        epf_contribution=86400,
        ppf_contribution=63600,     # Tops up 80C to 1.5L
        life_insurance_premium=0,
        self_health_insurance=25000,
        parent_health_insurance=50000,
        are_parents_senior_citizen=True,
        nps_contribution=50000,
        home_loan_interest=200000,
        home_loan_principal=100000,
        has_home_loan=True,
        savings_account_interest=8000,
        tds_deducted=150000
    )
    amit_report = check_deductions(amit)
    print_deduction_report(amit_report)

    # ── TEST CASE 3: Satish — 65 years old (Senior Citizen 80TTB check) ──
    satish = UserProfile(
        name="Satish",
        age=65,
        city="Delhi",
        is_metro=True,
        gross_salary=600000,
        savings_account_interest=15000,
        other_income=45000,  # e.g., FD Interest
        tds_deducted=0
    )
    satish_report = check_deductions(satish)
    print_deduction_report(satish_report)

