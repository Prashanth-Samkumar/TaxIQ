"""
ITR-2 Tax Calculator Tool - FY 2025-26 & FY 2026-27
Supports: Capital Gains (STCG/LTCG), Dividend Income, Surcharge Capping (15%), 
Section 87A Rebate limits, and Surcharge Marginal Relief.

Author: Tax Intelligence System
"""

import os
import sys
from dataclasses import dataclass

# Add current directory to path to ensure robust imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from itr1_calculator import (
    calculate_old_regime_tax,
    calculate_new_regime_tax,
    format_inr
)


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class ITR2Input:
    """
    Input to the ITR-2 tax calculator.
    All amounts in Indian Rupees (INR).
    """
    gross_salary: float           # Salary income before standard deduction
    age: int = 0                  # Age of the tax filer (to check senior status)
    hra_exemption: float = 0      # HRA exemption (old regime only)
    deduction_80c: float = 0      # Max 1,50,000 (old regime only)
    deduction_80d_self: float = 0 # Health insurance premium for self/family (old regime only)
    deduction_80d_parents: float = 0 # Health insurance premium for parents (old regime only)
    are_parents_senior_citizen: bool = False # Whether parents are senior citizens (above 60)
    deduction_80ccd1b: float = 0  # NPS extra contribution max 50,000 (old regime only)
    deduction_80e: float = 0      # Education loan interest (old regime only)
    deduction_80g: float = 0      # Donations (old regime only)
    deduction_80tta: float = 0    # Savings interest (non-seniors: max 10,000 u/s 80TTA)
    deduction_80ttb: float = 0    # Savings/FD interest (seniors: max 50,000 u/s 80TTB)
    deduction_24b: float = 0      # Home loan interest max 2,00,000 (old regime only)
    other_income: float = 0       # FD interest, other slab-rate sources
    dividend_income: float = 0    # Dividend income (slab rate, surcharge capped at 15%)
    
    # Capital Gains
    cg_stcg_equity: float = 0     # STCG u/s 111A (taxed at 20%, surcharge capped at 15%)
    cg_ltcg_equity: float = 0     # LTCG u/s 112A (taxed at 12.5% on gains > 1.25L, surcharge capped at 15%)
    cg_ltcg_other: float = 0      # LTCG u/s 112 (taxed at 12.5% flat e.g., gold/property, surcharge capped at 15%)
    cg_stcg_other: float = 0      # STCG other (added to slab income)
    
    tds_deducted: float = 0       # TDS already deducted


@dataclass
class ITR2Result:
    """
    Output from the ITR-2 tax calculator.
    """
    regime: str
    gross_total_income: float
    total_deductions: float
    taxable_normal_income: float
    tax_on_normal: float
    tax_on_dividend: float
    tax_on_stcg_equity: float
    tax_on_ltcg_equity: float
    tax_on_ltcg_other: float
    rebate_87a: float
    surcharge: float
    surcharge_relief: float
    cess: float
    total_tax_liability: float
    tds_deducted: float
    tax_payable_or_refund: float
    effective_tax_rate: float


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_surcharge_rates(income: float, regime: str) -> tuple[float, float]:
    """
    Get the surcharge rates for normal income and special rate/dividend income.
    Returns (rate_normal, rate_special).
    """
    if income <= 5000000:
        return 0.0, 0.0
    elif income <= 10000000:
        return 0.10, 0.10
    elif income <= 20000000:
        return 0.15, 0.15
    elif income <= 50000000:
        return 0.25, 0.15
    else:
        # Above 5 Cr
        rate_normal = 0.37 if regime == "old" else 0.25
        return rate_normal, 0.15


def compute_base_tax_and_surcharge(
    normal_taxable: float,
    cg_stcg_eq: float,
    cg_ltcg_eq: float,
    cg_ltcg_other: float,
    dividends: float,
    regime: str,
    override_surcharge_income: float = None
) -> tuple[float, float, float, float, float, float, float, float]:
    """
    Compute base taxes, 87A rebate, normal surcharge, and surcharge marginal relief.
    Returns:
        (tax_normal, tax_dividend, tax_stcg_eq, tax_ltcg_eq, tax_ltcg_other, rebate_87a, surcharge_total, surcharge_relief)
    """
    # 1. Base normal & dividend tax (slab rate)
    slab_taxable = normal_taxable + dividends
    if regime == "old":
        base_slab_tax, _ = calculate_old_regime_tax(slab_taxable)
    else:
        base_slab_tax, _ = calculate_new_regime_tax(slab_taxable)

    if slab_taxable > 0:
        tax_normal = base_slab_tax * (normal_taxable / slab_taxable)
        tax_dividend = base_slab_tax * (dividends / slab_taxable)
    else:
        tax_normal = 0.0
        tax_dividend = 0.0

    # 2. Special rate capital gains tax
    tax_stcg_eq = cg_stcg_eq * 0.20
    # Section 112A: 12.5% on gains above 1.25L
    tax_ltcg_eq = max(0.0, cg_ltcg_eq - 125000) * 0.125
    tax_ltcg_other = cg_ltcg_other * 0.125
    tax_special = tax_stcg_eq + tax_ltcg_eq + tax_ltcg_other

    # 3. Section 87A Rebate
    total_taxable_income = normal_taxable + dividends + cg_stcg_eq + cg_ltcg_eq + cg_ltcg_other
    rebate_87a = 0.0
    if regime == "old":
        if total_taxable_income <= 500000:
            rebate_87a = min(tax_normal + tax_dividend, 12500)
    else:  # new
        if total_taxable_income <= 1200000:
            rebate_87a = tax_normal + tax_dividend
        elif total_taxable_income <= 1270588:
            # New regime marginal relief for 87A
            excess_income = total_taxable_income - 1200000
            total_tax_before_rebate = tax_normal + tax_dividend + tax_special
            if total_tax_before_rebate > excess_income:
                rebate_87a = min(tax_normal + tax_dividend, total_tax_before_rebate - excess_income)

    tax_slab_after_rebate = max(0.0, tax_normal + tax_dividend - rebate_87a)
    total_tax_after_rebate = tax_slab_after_rebate + tax_special

    # 4. Surcharge
    surcharge_income = override_surcharge_income if override_surcharge_income is not None else total_taxable_income
    rate_normal, rate_special = get_surcharge_rates(surcharge_income, regime)

    # Pro-rate tax_normal after rebate for normal surcharge
    if (tax_normal + tax_dividend) > 0:
        tax_normal_after_rebate = tax_slab_after_rebate * (normal_taxable / (normal_taxable + dividends))
        tax_dividend_after_rebate = tax_slab_after_rebate * (dividends / (normal_taxable + dividends))
    else:
        tax_normal_after_rebate = 0.0
        tax_dividend_after_rebate = 0.0

    surcharge_normal = tax_normal_after_rebate * rate_normal
    surcharge_special = (tax_dividend_after_rebate + tax_special) * rate_special
    surcharge_total = surcharge_normal + surcharge_special

    # 5. Surcharge Marginal Relief
    surcharge_relief = 0.0
    if override_surcharge_income is None: # Only calculate relief in the actual run, not in threshold runs
        # Surcharge thresholds
        thresholds = [5000000, 10000000, 20000000]
        if regime == "old":
            thresholds.append(50000000)

        # Find the highest threshold crossed
        active_threshold = None
        for th in thresholds:
            if total_taxable_income > th:
                active_threshold = th

        if active_threshold is not None:
            # Scale inputs to active threshold
            factor = active_threshold / total_taxable_income
            # Compute tax + surcharge at threshold
            _, _, _, _, _, _, th_surcharge, _ = compute_base_tax_and_surcharge(
                normal_taxable * factor,
                cg_stcg_eq * factor,
                cg_ltcg_eq * factor,
                cg_ltcg_other * factor,
                dividends * factor,
                regime,
                override_surcharge_income=active_threshold
            )
            # Recompute base taxes at threshold for calculation
            th_slab_taxable = (normal_taxable + dividends) * factor
            if regime == "old":
                th_base_slab_tax, _ = calculate_old_regime_tax(th_slab_taxable)
            else:
                th_base_slab_tax, _ = calculate_new_regime_tax(th_slab_taxable)

            th_tax_stcg_eq = (cg_stcg_eq * factor) * 0.20
            th_tax_ltcg_eq = max(0.0, (cg_ltcg_eq * factor) - 125000) * 0.125
            th_tax_ltcg_other = (cg_ltcg_other * factor) * 0.125
            th_tax_special = th_tax_stcg_eq + th_tax_ltcg_eq + th_tax_ltcg_other

            # Compute threshold rebate u/s 87A
            th_total_income = active_threshold
            th_rebate = 0.0
            if regime == "old":
                if th_total_income <= 500000:
                    th_rebate = min(th_base_slab_tax, 12500)
            else:
                if th_total_income <= 1200000:
                    th_rebate = th_base_slab_tax
                elif th_total_income <= 1270588:
                    th_excess = th_total_income - 1200000
                    th_total_before_rebate = th_base_slab_tax + th_tax_special
                    if th_total_before_rebate > th_excess:
                        th_rebate = min(th_base_slab_tax, th_total_before_rebate - th_excess)

            th_tax_after_rebate = max(0.0, th_base_slab_tax - th_rebate) + th_tax_special
            total_tax_at_threshold = th_tax_after_rebate + th_surcharge

            # Maximum allowed tax + surcharge
            actual_tax_before_surcharge = total_tax_after_rebate
            excess_income = total_taxable_income - active_threshold
            max_allowed = total_tax_at_threshold + excess_income

            if (actual_tax_before_surcharge + surcharge_total) > max_allowed:
                surcharge_relief = (actual_tax_before_surcharge + surcharge_total) - max_allowed
                surcharge_total = max(0.0, surcharge_total - surcharge_relief)

    return tax_normal, tax_dividend, tax_stcg_eq, tax_ltcg_eq, tax_ltcg_other, rebate_87a, surcharge_total, surcharge_relief


# ─────────────────────────────────────────────
# MAIN CALCULATION FUNCTION
# ─────────────────────────────────────────────

def calculate_itr2_tax(inputs: ITR2Input, regime: str = "both") -> dict:
    """
    Main entry point for ITR-2 tax calculations.
    """
    results = {}
    
    # ── GROSS TOTAL INCOME ──
    # Normal Gross Total Income (Salary + Other + Dividends + STCG other)
    # Special gains (STCG 111A, LTCG 112A, LTCG 112) are taxed separately at special rates.
    gross_total_income = (
        inputs.gross_salary + 
        inputs.other_income + 
        inputs.dividend_income + 
        inputs.cg_stcg_equity + 
        inputs.cg_ltcg_equity + 
        inputs.cg_ltcg_other + 
        inputs.cg_stcg_other
    )

    for r in ["old", "new"]:
        if regime != "both" and regime != r:
            continue
            
        # Determine standard deduction
        if r == "old":
            std_deduction = min(inputs.gross_salary, 50000)

            # Section 80D Health Insurance Capping
            self_80d_limit = 50000 if inputs.age >= 60 else 25000
            parent_80d_limit = 50000 if inputs.are_parents_senior_citizen else 25000
            utilized_80d = min(inputs.deduction_80d_self, self_80d_limit) + min(inputs.deduction_80d_parents, parent_80d_limit)

            # Section 80TTA vs 80TTB Interest Exemption
            if inputs.age >= 60:
                interest_deduction = min(inputs.deduction_80ttb, 50000)
            else:
                interest_deduction = min(inputs.deduction_80tta, 10000)

            total_deductions = (
                std_deduction +
                inputs.hra_exemption +
                min(inputs.deduction_80c, 150000) +
                utilized_80d +
                min(inputs.deduction_80ccd1b, 50000) +
                inputs.deduction_80e +
                inputs.deduction_80g +
                interest_deduction +
                min(inputs.deduction_24b, 200000)
            )
        else:
            std_deduction = min(inputs.gross_salary, 75000)
            total_deductions = std_deduction

        # Gross slab-rate taxable income (Normal + STCG other + Dividends)
        # Deductions can only reduce slab-taxable income
        normal_gross_total = inputs.gross_salary + inputs.other_income + inputs.cg_stcg_other
        normal_taxable = max(0.0, normal_gross_total - total_deductions)
        
        # Compute taxes, rebate, surcharge, and surcharge relief
        (
            tax_normal,
            tax_dividend,
            tax_stcg_eq,
            tax_ltcg_eq,
            tax_ltcg_other,
            rebate_87a,
            surcharge,
            surcharge_relief
        ) = compute_base_tax_and_surcharge(
            normal_taxable=normal_taxable,
            cg_stcg_eq=inputs.cg_stcg_equity,
            cg_ltcg_eq=inputs.cg_ltcg_equity,
            cg_ltcg_other=inputs.cg_ltcg_other,
            dividends=inputs.dividend_income,
            regime=r
        )

        # Total tax after rebate (before surcharge and cess)
        total_base_tax = tax_normal + tax_dividend + tax_stcg_eq + tax_ltcg_eq + tax_ltcg_other
        tax_after_rebate = max(0.0, total_base_tax - rebate_87a)
        
        # Health & Education Cess (4% on tax after rebate + surcharge)
        cess = (tax_after_rebate + surcharge) * 0.04
        
        total_tax_liability = tax_after_rebate + surcharge + cess
        tax_payable = total_tax_liability - inputs.tds_deducted
        effective_rate = (total_tax_liability / gross_total_income * 100) if gross_total_income > 0 else 0

        results[r] = ITR2Result(
            regime="Old Regime" if r == "old" else "New Regime",
            gross_total_income=gross_total_income,
            total_deductions=total_deductions,
            taxable_normal_income=normal_taxable,
            tax_on_normal=round(tax_normal, 2),
            tax_on_dividend=round(tax_dividend, 2),
            tax_on_stcg_equity=round(tax_stcg_eq, 2),
            tax_on_ltcg_equity=round(tax_ltcg_eq, 2),
            tax_on_ltcg_other=round(tax_ltcg_other, 2),
            rebate_87a=round(rebate_87a, 2),
            surcharge=round(surcharge, 2),
            surcharge_relief=round(surcharge_relief, 2),
            cess=round(cess, 2),
            total_tax_liability=round(total_tax_liability, 2),
            tds_deducted=inputs.tds_deducted,
            tax_payable_or_refund=round(tax_payable, 2),
            effective_tax_rate=round(effective_rate, 2)
        )
        
    return results


# ─────────────────────────────────────────────
# PRETTY PRINT HELPER
# ─────────────────────────────────────────────

def print_itr2_result(result: ITR2Result):
    """Print readable ITR-2 results."""
    print(f"\n{'='*60}")
    print(f"  ITR-2 Calculator Results - {result.regime} - FY 2025-26")
    print(f"{'='*60}")
    print(f"  Gross Total Income        : {format_inr(result.gross_total_income)}")
    print(f"  Total Deductions          : {format_inr(result.total_deductions)}")
    print(f"  Taxable Normal Income     : {format_inr(result.taxable_normal_income)}")
    print(f"\n  Tax Breakdown by Income Head:")
    print(f"    Normal Slab Income Tax  : {format_inr(result.tax_on_normal)}")
    print(f"    Dividend Income Tax     : {format_inr(result.tax_on_dividend)}")
    print(f"    STCG Equity Tax (111A)  : {format_inr(result.tax_on_stcg_equity)}")
    print(f"    LTCG Equity Tax (112A)  : {format_inr(result.tax_on_ltcg_equity)}")
    print(f"    LTCG Other Tax (112)    : {format_inr(result.tax_on_ltcg_other)}")
    print(f"\n  Rebates & Surcharges:")
    print(f"    Section 87A Rebate      : {format_inr(result.rebate_87a)}")
    print(f"    Surcharge Liability     : {format_inr(result.surcharge)}")
    if result.surcharge_relief > 0:
        print(f"    Surcharge Relief        : {format_inr(result.surcharge_relief)}")
    print(f"    Health & Education Cess : {format_inr(result.cess)}")
    print(f"  Total Tax Liability       : {format_inr(result.total_tax_liability)}")
    print(f"  TDS Already Deducted      : {format_inr(result.tds_deducted)}")
    if result.tax_payable_or_refund >= 0:
        print(f"  Tax Payable               : {format_inr(result.tax_payable_or_refund)}")
    else:
        print(f"  Refund Due                : {format_inr(abs(result.tax_payable_or_refund))}")
    print(f"  Effective Tax Rate        : {result.effective_tax_rate}%")
    print(f"{'='*60}")


# ─────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n📊 ITR-2 TAX CALCULATOR TEST SUITE")
    print("Please verify all outputs with a CA\n")

    # ── TEST CASE 1: Capital Gains and Section 87A Rebate exclusion check ──
    # Salary ₹8L, STCG Equity ₹1L. Total Income ₹9L.
    # Standard deduction ₹75,000. Taxable Normal Income ₹7.25L.
    # Slab tax under New Regime: 5% of 3.25L = 16,250.
    # STCG Equity tax: 20% of 1L = 20,000.
    # Total income is 9L (<= 12L limit for 87A).
    # Normal tax (16,250) is fully rebated. STCG tax (20,000) CANNOT be rebated.
    # Cess = 20,000 * 0.04 = 800. Total tax = 20,800.
    print("TEST CASE 1: Karan — Salary 8L, STCG Equity 1L (Rebate 87A exclusion check)")
    karan = ITR2Input(
        gross_salary=800000,
        age=30,
        cg_stcg_equity=100000
    )
    karan_res = calculate_itr2_tax(karan, regime="new")
    for r in karan_res.values():
        print_itr2_result(r)
        assert r.rebate_87a == 16250.0, f"Expected 87A rebate of 16,250, got {r.rebate_87a}"
        assert r.total_tax_liability == 20800.0, f"Expected total tax of 20,800, got {r.total_tax_liability}"

    # ── TEST CASE 2: High income earner with capped surcharge rates ──
    # Normal income ₹2.5 Cr, CG (111A/112/112A) ₹60 Lakhs. Total Income ₹3.1 Cr.
    # Surcharge on Normal Tax is 25%.
    # Surcharge on Special Rate CG Tax is capped at 15%.
    print("TEST CASE 2: High Income — Salary 2.5 Cr, STCG Equity 60 Lakhs (Surcharge capping check)")
    high_inc = ITR2Input(
        gross_salary=25000000,
        age=45,
        cg_stcg_equity=6000000
    )
    high_inc_res = calculate_itr2_tax(high_inc, regime="both")
    for r in high_inc_res.values():
        print_itr2_result(r)
        
        # Verify New Regime Surcharge logic:
        # gross_salary = 2.5Cr. Standard deduction = 75k. Taxable Normal = 24,925,000.
        # Slabs tax:
        # 4-8L (20k), 8-12L (40k), 12-16L (60k), 16-20L (80k), 20-24L (1L), Above 24L (30% of 22,525,000 = 6,757,500).
        # Total normal tax = 7,057,500.
        # STCG Equity tax = 6,000,000 * 20% = 1,200,000.
        # Total income is 3.1Cr, which is in (2Cr, 5Cr] bracket (25% normal surcharge rate).
        # Surcharge on normal: 7,057,500 * 25% = 1,764,375.
        # Surcharge on STCG Equity (capped at 15%): 1,200,000 * 15% = 180,000.
        # Total surcharge = 1,764,375 + 180,000 = 1,944,375.
        # Cess = (total tax (8,257,500) + surcharge (1,944,375)) * 4% = 408,075.
        # Total tax liability = 8,257,500 + 1,944,375 + 408,075 = 10,609,950.
        if r.regime == "New Regime":
            assert r.surcharge == 1944375.0, f"Expected surcharge of 1,944,375, got {r.surcharge}"
            assert r.total_tax_liability == 10609950.0, f"Expected total tax liability of 10,609,950, got {r.total_tax_liability}"

    # ── TEST CASE 3: Surcharge Marginal Relief at 50 Lakhs limit ──
    # Taxable Normal Income ₹50,50,000 (Salary 51.25L - standard deduction 75K).
    # Total Income ₹50.5 Lakhs net taxable (crossing 50L threshold).
    # Verifies that total tax + surcharge does not exceed tax at 50L + excess income of 50K.
    print("TEST CASE 3: Amit — Salary 51.25L, no investments (Surcharge marginal relief at 50L)")
    amit = ITR2Input(
        gross_salary=5125000,
        age=35
    )
    amit_res = calculate_itr2_tax(amit, regime="new")
    for r in amit_res.values():
        print_itr2_result(r)
        # Taxable normal = 5,050,000. Slabs tax = 1,095,000.
        # Surcharge (normal 10%) = 109,500. Total tax + surcharge = 1,204,500.
        # Tax at threshold 50L: taxable = 5,000,000. Slabs tax = 1,080,000. Surcharge = 0.
        # Excess income = 5,050,000 - 5,000,000 = 50,000.
        # Max allowed = 1,080,000 + 50,000 = 1,130,000.
        # Actual (1,204,500) > Max (1,130,000), so relief applies.
        # Relief = 1,204,500 - 1,130,000 = 74,500.
        # Surcharge final = 109,500 - 74,500 = 35,000.
        # Cess = (1,095,000 + 35,000) * 0.04 = 45,200.
        # Total tax liability = 1,095,000 + 35,000 + 45,200 = 1,175,200.
        assert r.surcharge == 35000.0, f"Expected surcharge of 35,000, got {r.surcharge}"
        assert r.total_tax_liability == 1175200.0, f"Expected total tax liability of 1,175,200, got {r.total_tax_liability}"

    print("\n🎉 ALL ITR-2 TESTS COMPLETED AND VERIFIED CORRECTLY!")
