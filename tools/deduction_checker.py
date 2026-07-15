"""
Deduction Checker Tool - FY 2025-26
Checks all deductions a salaried person is eligible for,
how much they have used, and how much room is left.

Only relevant for OLD regime. New regime does not allow these deductions.

"""


from .schemas import UserProfile, DeductionItem, DeductionReport


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
    return max(0, exemption)



def check_deductions(profile: UserProfile) -> DeductionReport:
    """
    Main deduction checker function.
    Goes through every deduction, checks eligibility,
    calculates utilized and remaining amounts.
    """

    items = []
    missed_opportunities = []
    alerts = []

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

    hra_exemption = calculate_hra_exemption(profile)
    hra_missed = profile.rent_paid_monthly > 0 and profile.hra_received == 0
    hra_not_claiming = profile.hra_received > 0 and profile.rent_paid_monthly == 0

    hra_message = ""
    if hra_exemption > 0:
        hra_message = f"HRA exemption of Rs. {hra_exemption:,.0f} applicable. Submit rent receipts to employer."
    elif hra_missed:
        hra_message = "You pay rent but HRA is not in your salary structure. Negotiate with employer to restructure CTC."
        missed_opportunities.append("HRA exemption - restructure salary to include HRA component")
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
        alerts.append(f"80C: Rs. {remaining_80c:,.0f} limit unused. Invest in ELSS, PPF, or top up EPF voluntarily to save more tax.")

    items.append(DeductionItem(
        section="80C",
        name="Tax Saving Investments (ELSS, PPF, EPF, LIC etc.)",
        max_limit=150000,
        utilized=utilized_80c,
        remaining=remaining_80c,
        is_eligible=True,
        message=f"Used Rs. {utilized_80c:,.0f} of Rs. 1,50,000 limit. Rs. {remaining_80c:,.0f} remaining.",
        is_missed=total_80c == 0
    ))

    self_80d_limit = 50000 if profile.age >= 60 else 25000
    parent_80d_limit = 50000 if profile.are_parents_senior_citizen else 25000

    utilized_80d_self = min(profile.self_health_insurance, self_80d_limit)
    utilized_80d_parent = min(profile.parent_health_insurance, parent_80d_limit)
    total_utilized_80d = utilized_80d_self + utilized_80d_parent
    total_80d_limit = self_80d_limit + parent_80d_limit
    remaining_80d = total_80d_limit - total_utilized_80d

    if profile.self_health_insurance == 0:
        missed_opportunities.append(f"80D: No self health insurance. Buy a policy to claim up to Rs. 25,000 deduction.")

    if profile.parent_health_insurance == 0:
        parent_limit_str = "Rs. 50,000" if profile.are_parents_senior_citizen else "Rs. 25,000"
        missed_opportunities.append(f"80D: No parent health insurance. Buy a policy to claim up to {parent_limit_str} deduction.")

    items.append(DeductionItem(
        section="80D",
        name="Health Insurance Premium",
        max_limit=total_80d_limit,
        utilized=total_utilized_80d,
        remaining=remaining_80d,
        is_eligible=True,
        message=f"Self/family limit: Rs. 25,000. Parent limit: Rs. {parent_80d_limit:,.0f}. Used: Rs. {total_utilized_80d:,.0f}. Remaining: Rs. {remaining_80d:,.0f}.",
        is_missed=total_utilized_80d == 0
    ))

    utilized_nps = min(profile.nps_contribution, 50000)
    remaining_nps = max(0, 50000 - profile.nps_contribution)

    if profile.nps_contribution == 0:
        missed_opportunities.append("80CCD1B: No NPS investment. Invest up to Rs. 50,000 for additional deduction OVER AND ABOVE 80C limit.")

    items.append(DeductionItem(
        section="80CCD1B",
        name="NPS (National Pension Scheme) - Extra Deduction",
        max_limit=50000,
        utilized=utilized_nps,
        remaining=remaining_nps,
        is_eligible=True,
        message=f"This is SEPARATE from 80C. Additional Rs. 50,000 deduction available. Used: Rs. {utilized_nps:,.0f}. Remaining: Rs. {remaining_nps:,.0f}.",
        is_missed=profile.nps_contribution == 0
    ))

    if profile.education_loan_interest > 0:
        items.append(DeductionItem(
            section="80E",
            name="Education Loan Interest",
            max_limit=profile.education_loan_interest,
            utilized=profile.education_loan_interest,
            remaining=0,
            is_eligible=True,
            message=f"Full interest of Rs. {profile.education_loan_interest:,.0f} deductible. No upper limit. Available for 8 years.",
            is_missed=False
        ))

    total_donations = profile.donations_100_percent + (profile.donations_50_percent * 0.5)
    if total_donations > 0:
        items.append(DeductionItem(
            section="80G",
            name="Donations to Charitable Institutions",
            max_limit=total_donations,
            utilized=total_donations,
            remaining=0,
            is_eligible=True,
            message=f"Deductible donation amount: Rs. {total_donations:,.0f}. Keep receipts and 80G certificates.",
            is_missed=False
        ))

    if profile.age >= 60:
        interest_income = profile.savings_account_interest + profile.other_income
        utilized_80ttb = min(interest_income, 50000)
        items.append(DeductionItem(
            section="80TTB",
            name="Interest on Deposits for Senior Citizens (Savings/FD)",
            max_limit=50000,
            utilized=utilized_80ttb,
            remaining=max(0.0, 50000 - interest_income),
            is_eligible=True,
            message=f"Senior citizen interest deduction u/s 80TTB (Savings/FD) up to Rs. 50,000. Utilized: Rs. {utilized_80ttb:,.0f}. Remaining: Rs. {max(0.0, 50000 - interest_income):,.0f}.",
            is_missed=interest_income == 0
        ))
    else:
        utilized_80tta = min(profile.savings_account_interest, 10000)
        items.append(DeductionItem(
            section="80TTA",
            name="Savings Account Interest",
            max_limit=10000,
            utilized=utilized_80tta,
            remaining=max(0.0, 10000 - profile.savings_account_interest),
            is_eligible=True,
            message=f"Savings interest up to Rs. 10,000 is exempt. Your interest: Rs. {profile.savings_account_interest:,.0f}. Exempt: Rs. {utilized_80tta:,.0f}.",
            is_missed=profile.savings_account_interest == 0
        ))

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
            message=f"Home loan interest deduction up to Rs. 2,00,000. Used: Rs. {utilized_24b:,.0f}.",
            is_missed=False
        ))

    total_possible = sum(item.max_limit for item in items)
    total_utilized = sum(item.utilized for item in items)
    total_remaining = sum(item.remaining for item in items if item.remaining > 0)

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



def print_deduction_report(report: DeductionReport):
    """Print a clean readable deduction report."""
    print(f"\n{'='*55}")
    print(f"  DEDUCTION REPORT FOR: {report.user_name}")
    print(f"  FY 2025-26 | Old Regime")
    print(f"{'='*55}")
    print(f"  Total Deductions Possible  : Rs. {report.total_possible_deductions:,.0f}")
    print(f"  Total Utilized             : Rs. {report.total_utilized_deductions:,.0f}")
    print(f"  Total Remaining            : Rs. {report.total_remaining_deductions:,.0f}")
    print(f"  Potential Tax Saving Left  : Rs. {report.potential_tax_saving:,.0f} (approx)")

    print(f"\n  DEDUCTION BREAKDOWN:")
    print(f"  {'-'*50}")
    for item in report.items:
        status = "[YES]" if item.utilized > 0 else "[NO]"
        print(f"\n  {status} {item.section} - {item.name}")
        print(f"     Limit    : Rs. {item.max_limit:,.0f}")
        print(f"     Utilized : Rs. {item.utilized:,.0f}")
        if item.remaining > 0:
            print(f"     Remaining: Rs. {item.remaining:,.0f} <- ACTION NEEDED")
        print(f"     Note     : {item.message}")

    if report.missed_opportunities:
        print(f"\n  [ALERT] MISSED OPPORTUNITIES:")
        for i, opp in enumerate(report.missed_opportunities, 1):
            print(f"     {i}. {opp}")

    if report.alerts:
        print(f"\n  [WARNING] ALERTS:")
        for alert in report.alerts:
            print(f"     -> {alert}")

    print(f"\n{'='*55}\n")



