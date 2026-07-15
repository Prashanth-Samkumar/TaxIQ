"""
Tax Calculator Tool - FY 2025-26 (AY 2026-27)
Supports Old Regime and New Regime
Covers: Slabs, Surcharge, Cess, Rebate 87A

"""

from dataclasses import dataclass
from .schemas import TaxInput, TaxResult


def calculate_old_regime_tax(taxable_income: float, age: int = 0) -> tuple[float, list]:
    """
    Calculate tax as per OLD regime slabs for FY 2025-26.
    Supports age-based exemption limits:
    - Below 60 years: Nil up to 2.5L
    - Senior Citizens (60-79 years): Nil up to 3.0L
    - Super Senior Citizens (80+ years): Nil up to 5.0L
    """
    tax = 0
    breakdown = []

    if age >= 80:
        slabs = [
            (500000, 0.00, "Up to Rs. 5,00,000"),
            (500000, 0.20, "Rs. 5,00,001 to Rs. 10,00,000 @ 20%"),
            (float('inf'), 0.30, "Above Rs. 10,00,000 @ 30%"),
        ]
    elif age >= 60:
        slabs = [
            (300000, 0.00, "Up to Rs. 3,00,000"),
            (200000, 0.05, "Rs. 3,00,001 to Rs. 5,00,000 @ 5%"),
            (500000, 0.20, "Rs. 5,00,001 to Rs. 10,00,000 @ 20%"),
            (float('inf'), 0.30, "Above Rs. 10,00,000 @ 30%"),
        ]
    else:
        slabs = [
            (250000, 0.00, "Up to Rs. 2,50,000"),
            (250000, 0.05, "Rs. 2,50,001 to Rs. 5,00,000 @ 5%"),
            (500000, 0.20, "Rs. 5,00,001 to Rs. 10,00,000 @ 20%"),
            (float('inf'), 0.30, "Above Rs. 10,00,000 @ 30%"),
        ]

    remaining = taxable_income

    for slab_limit, rate, label in slabs:
        if remaining <= 0:
            break
        taxable_in_slab = min(remaining, slab_limit)
        tax_in_slab = taxable_in_slab * rate
        tax += tax_in_slab
        remaining -= taxable_in_slab
        if taxable_in_slab > 0 and rate > 0:
            breakdown.append({
                "slab": label,
                "amount": taxable_in_slab,
                "tax": tax_in_slab
            })

    return tax, breakdown


def calculate_new_regime_tax(taxable_income: float) -> tuple[float, list]:
    """
    Calculate tax as per NEW regime slabs for FY 2025-26.
    Budget 2025 updated slabs (effective FY 2025-26):

    Slabs:
    - Up to 4,00,000        : Nil
    - 4,00,001 to 8,00,000  : 5%
    - 8,00,001 to 12,00,000 : 10%
    - 12,00,001 to 16,00,000: 15%
    - 16,00,001 to 20,00,000: 20%
    - 20,00,001 to 24,00,000: 25%
    - Above 24,00,000       : 30%

    Note: Rebate 87A under new regime is up to 12,00,000 taxable income
    making effective tax zero up to 12,00,000.
    """
    tax = 0
    breakdown = []

    slabs = [
        (400000,      0.00, "Up to Rs. 4,00,000"),
        (400000,      0.05, "Rs. 4,00,001 to Rs. 8,00,000 @ 5%"),
        (400000,      0.10, "Rs. 8,00,001 to Rs. 12,00,000 @ 10%"),
        (400000,      0.15, "Rs. 12,00,001 to Rs. 16,00,000 @ 15%"),
        (400000,      0.20, "Rs. 16,00,001 to Rs. 20,00,000 @ 20%"),
        (400000,      0.25, "Rs. 20,00,001 to Rs. 24,00,000 @ 25%"),
        (float('inf'), 0.30, "Above Rs. 24,00,000 @ 30%"),
    ]

    remaining = taxable_income

    for slab_limit, rate, label in slabs:
        if remaining <= 0:
            break
        taxable_in_slab = min(remaining, slab_limit)
        tax_in_slab = taxable_in_slab * rate
        tax += tax_in_slab
        remaining -= taxable_in_slab
        if taxable_in_slab > 0 and rate > 0:
            breakdown.append({
                "slab": label,
                "amount": taxable_in_slab,
                "tax": tax_in_slab
            })

    return tax, breakdown


def calculate_rebate_87a(tax: float, taxable_income: float, regime: str) -> float:
    """
    Section 87A Rebate.
    
    Old Regime : Rebate up to Rs 12,500 if taxable income <= 5,00,000
    New Regime : Rebate up to Rs 60,000 if taxable income <= 12,00,000,
                 with marginal relief if taxable income marginally exceeds 12,00,000.
    """
    if regime == "old":
        if taxable_income <= 500000:
            return min(tax, 12500)
    elif regime == "new":
        if taxable_income <= 1200000:
            return tax
        else:
            excess_income = taxable_income - 1200000
            if tax > excess_income:
                return tax - excess_income
    return 0


def calculate_tax(inputs: TaxInput, regime: str = "both") -> dict:
    """
    Main tax calculator function.
    
    Args:
        inputs  : TaxInput dataclass with all income and deduction details
        regime  : "old", "new", or "both"
    
    Returns:
        Dictionary with TaxResult for requested regime(s)
    """

    results = {}

    gross_total_income = inputs.gross_salary + inputs.other_income

    if regime in ["old", "both"]:

        std_deduction_old = min(inputs.gross_salary, 50000)

        self_80d_limit = 50000 if inputs.age >= 60 else 25000
        parent_80d_limit = 50000 if inputs.are_parents_senior_citizen else 25000
        utilized_80d = min(inputs.deduction_80d_self, self_80d_limit) + min(inputs.deduction_80d_parents, parent_80d_limit)

        if inputs.age >= 60:
            interest_deduction = min(inputs.deduction_80ttb, 50000)
        else:
            interest_deduction = min(inputs.deduction_80tta, 10000)

        total_deductions = (
            std_deduction_old +
            inputs.hra_exemption +
            min(inputs.deduction_80c, 150000) +
            utilized_80d +
            min(inputs.deduction_80ccd1b, 50000) +
            inputs.deduction_80e +
            inputs.deduction_80g +
            interest_deduction +
            min(inputs.deduction_24b, 200000)
        )

        taxable_income_old = max(0, gross_total_income - total_deductions)
        tax_old, breakdown_old = calculate_old_regime_tax(taxable_income_old, inputs.age)
        tax_after_surcharge_old = tax_old
        rebate_old = calculate_rebate_87a(tax_after_surcharge_old, taxable_income_old, "old")
        tax_after_rebate_old = max(0, tax_after_surcharge_old - rebate_old)
        cess_old = tax_after_rebate_old * 0.04
        total_tax_old = tax_after_rebate_old + cess_old
        tax_payable_old = total_tax_old - inputs.tds_deducted
        effective_rate_old = (total_tax_old / gross_total_income * 100) if gross_total_income > 0 else 0

        results["old"] = TaxResult(
            regime="Old Regime",
            gross_total_income=gross_total_income,
            total_deductions=total_deductions,
            taxable_income=taxable_income_old,
            tax_before_cess=tax_old,

            tax_after_surcharge=tax_after_surcharge_old,
            rebate_87a=rebate_old,
            cess=cess_old,
            total_tax=round(total_tax_old, 2),
            tds_deducted=inputs.tds_deducted,
            tax_payable_or_refund=round(tax_payable_old, 2),
            effective_tax_rate=round(effective_rate_old, 2),
            slab_breakdown=breakdown_old
        )

    if regime in ["new", "both"]:

        std_deduction_new = min(inputs.gross_salary, 75000)
        total_deductions_new = std_deduction_new

        taxable_income_new = max(0, gross_total_income - total_deductions_new)
        tax_new, breakdown_new = calculate_new_regime_tax(taxable_income_new)
        tax_after_surcharge_new = tax_new 
        rebate_new = calculate_rebate_87a(tax_after_surcharge_new, taxable_income_new, "new")
        tax_after_rebate_new = max(0, tax_after_surcharge_new - rebate_new)
        cess_new = tax_after_rebate_new * 0.04
        total_tax_new = tax_after_rebate_new + cess_new
        tax_payable_new = total_tax_new - inputs.tds_deducted
        effective_rate_new = (total_tax_new / gross_total_income * 100) if gross_total_income > 0 else 0

        results["new"] = TaxResult(
            regime="New Regime",
            gross_total_income=gross_total_income,
            total_deductions=total_deductions_new,
            taxable_income=taxable_income_new,
            tax_before_cess=tax_new,
            tax_after_surcharge=tax_after_surcharge_new,
            rebate_87a=rebate_new,
            cess=cess_new,
            total_tax=round(total_tax_new, 2),
            tds_deducted=inputs.tds_deducted,
            tax_payable_or_refund=round(tax_payable_new, 2),
            effective_tax_rate=round(effective_rate_new, 2),
            slab_breakdown=breakdown_new
        )

    return results







def format_inr(amount: float) -> str:
    """Format number as Indian Rupees with commas."""
    return f"Rs. {amount:,.2f}"


def print_tax_result(result: TaxResult):
    """Print a clean readable tax result."""
    print(f"\n{'='*60}")
    print(f"  ITR-1 Calculator Results - {result.regime} - FY 2025-26")
    print(f"{'='*60}")
    print(f"  Gross Total Income        : {format_inr(result.gross_total_income)}")
    print(f"  Total Deductions          : {format_inr(result.total_deductions)}")
    print(f"  Taxable Income            : {format_inr(result.taxable_income)}")
    print(f"\n  Slab-wise Tax Breakdown:")
    for slab in result.slab_breakdown:
        print(f"    {slab['slab']}")
        print(f"      Amount : {format_inr(slab['amount'])}")
        print(f"      Tax    : {format_inr(slab['tax'])}")
    print(f"\n  Tax Before Cess           : {format_inr(result.tax_before_cess)}")
    print(f"  Rebate u/s 87A            : {format_inr(result.rebate_87a)}")
    print(f"  Health & Education Cess   : {format_inr(result.cess)}")
    print(f"  Total Tax Liability       : {format_inr(result.total_tax)}")
    print(f"  TDS Already Deducted      : {format_inr(result.tds_deducted)}")
    if result.tax_payable_or_refund >= 0:
        print(f"  Tax Payable               : {format_inr(result.tax_payable_or_refund)}")
    else:
        print(f"  Refund Due                : {format_inr(abs(result.tax_payable_or_refund))}")
    print(f"  Effective Tax Rate        : {result.effective_tax_rate}%")
    print(f"{'='*60}")





