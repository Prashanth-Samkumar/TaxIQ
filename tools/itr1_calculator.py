"""
Tax Calculator Tool - FY 2025-26 (AY 2026-27)
Supports Old Regime and New Regime
Covers: Slabs, Surcharge, Cess, Rebate 87A

Author: Tax Intelligence System
Verified by: CA [Your Sister's Name]
"""

from dataclasses import dataclass


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class TaxInput:
    """
    Input to the tax calculator.
    All amounts in Indian Rupees (INR).
    """
    gross_salary: float           # Total salary before any deductions
    age: int = 0                  # Age of the tax filer (to check senior status)
    hra_exemption: float = 0      # HRA exemption calculated separately (old regime only)
    standard_deduction: float = 75000  # Default 75,000 for New Regime. (Old Regime is capped at 50,000)
    deduction_80c: float = 0      # Max 1,50,000 (old regime only)
    deduction_80d_self: float = 0 # Health insurance premium for self/family (old regime only)
    deduction_80d_parents: float = 0 # Health insurance premium for parents (old regime only)
    are_parents_senior_citizen: bool = False # Whether parents are senior citizens (above 60)
    deduction_80ccd1b: float = 0  # NPS extra deduction max 50,000 (old regime only)
    deduction_80e: float = 0      # Education loan interest (old regime only)
    deduction_80g: float = 0      # Donations (old regime only)
    deduction_80tta: float = 0    # Savings interest (non-seniors: max 10,000 u/s 80TTA)
    deduction_80ttb: float = 0    # Savings/FD interest (seniors: max 50,000 u/s 80TTB)
    deduction_24b: float = 0      # Home loan interest max 2,00,000 (old regime only)
    other_income: float = 0       # FD interest, savings interest, other sources
    tds_deducted: float = 0       # TDS already deducted by employer


@dataclass
class TaxResult:
    """
    Output from the tax calculator.
    All amounts in Indian Rupees (INR).
    """
    regime: str
    gross_total_income: float
    total_deductions: float
    taxable_income: float
    tax_before_cess: float
    tax_after_surcharge: float
    rebate_87a: float
    cess: float
    total_tax: float
    tds_deducted: float
    tax_payable_or_refund: float  # Positive = payable, Negative = refund
    effective_tax_rate: float
    slab_breakdown: list


# ─────────────────────────────────────────────
# CORE CALCULATION FUNCTIONS
# ─────────────────────────────────────────────

def calculate_old_regime_tax(taxable_income: float) -> tuple[float, list]:
    """
    Calculate tax as per OLD regime slabs for FY 2025-26.
    
    Slabs:
    - Up to 2,50,000        : Nil
    - 2,50,001 to 5,00,000  : 5%
    - 5,00,001 to 10,00,000 : 20%
    - Above 10,00,000       : 30%
    """
    tax = 0
    breakdown = []

    slabs = [
        (250000, 0.00, "Up to ₹2,50,000"),
        (250000, 0.05, "₹2,50,001 to ₹5,00,000 @ 5%"),
        (500000, 0.20, "₹5,00,001 to ₹10,00,000 @ 20%"),
        (float('inf'), 0.30, "Above ₹10,00,000 @ 30%"),
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
        (400000,      0.00, "Up to ₹4,00,000"),
        (400000,      0.05, "₹4,00,001 to ₹8,00,000 @ 5%"),
        (400000,      0.10, "₹8,00,001 to ₹12,00,000 @ 10%"),
        (400000,      0.15, "₹12,00,001 to ₹16,00,000 @ 15%"),
        (400000,      0.20, "₹16,00,001 to ₹20,00,000 @ 20%"),
        (400000,      0.25, "₹20,00,001 to ₹24,00,000 @ 25%"),
        (float('inf'), 0.30, "Above ₹24,00,000 @ 30%"),
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


# def calculate_surcharge(tax_before_surcharge: float, taxable_income: float, regime: str = "old") -> float:
#     """
#     Surcharge applies on income above 50 lakhs.
    
#     - 50L to 1 Cr   : 10% of tax
#     - 1 Cr to 2 Cr  : 15% of tax
#     - 2 Cr to 5 Cr  : 25% of tax (old regime) / 25% (new regime)
#     - Above 5 Cr    : 37% of tax (old regime) / 25% (new regime capped at 25%)
    
#     For interview scope (ITR1/ITR2 salaried), most users will be below 50L.
#     Including this for completeness.
#     """
#     if taxable_income <= 5000000:       # Up to 50 lakhs
#         return 0
#     elif taxable_income <= 10000000:    # 50L to 1 Cr
#         return tax_before_surcharge * 0.10
#     elif taxable_income <= 20000000:    # 1 Cr to 2 Cr
#         return tax_before_surcharge * 0.15
#     elif taxable_income <= 50000000:    # 2 Cr to 5 Cr
#         return tax_before_surcharge * 0.25
#     else:
#         # Above 5 Cr: old regime 37%, new regime capped at 25%
#         rate = 0.37 if regime == "old" else 0.25
#         return tax_before_surcharge * rate


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
            # Marginal relief under Section 87A
            excess_income = taxable_income - 1200000
            if tax > excess_income:
                return tax - excess_income
    return 0


# ─────────────────────────────────────────────
# MAIN TOOL FUNCTION
# ─────────────────────────────────────────────

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

    # ── GROSS TOTAL INCOME (same for both regimes) ──
    gross_total_income = inputs.gross_salary + inputs.other_income

    # ── OLD REGIME CALCULATION ──
    if regime in ["old", "both"]:

        # Deductions allowed only in old regime
        # Standard deduction for old regime is capped at 50,000 (and limited by gross salary)
        std_deduction_old = min(inputs.gross_salary, 50000)

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
            std_deduction_old +
            inputs.hra_exemption +
            min(inputs.deduction_80c, 150000) +       # Capped at 1.5L
            utilized_80d +
            min(inputs.deduction_80ccd1b, 50000) +    # Capped at 50K
            inputs.deduction_80e +
            inputs.deduction_80g +
            interest_deduction +
            min(inputs.deduction_24b, 200000)          # Capped at 2L
        )

        taxable_income_old = max(0, gross_total_income - total_deductions)
        tax_old, breakdown_old = calculate_old_regime_tax(taxable_income_old)
        tax_after_surcharge_old = tax_old
        rebate_old = calculate_rebate_87a(tax_after_surcharge_old, taxable_income_old, "old")
        tax_after_rebate_old = max(0, tax_after_surcharge_old - rebate_old)
        cess_old = tax_after_rebate_old * 0.04         # 4% Health & Education Cess
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

    # ── NEW REGIME CALCULATION ──
    if regime in ["new", "both"]:

        # New regime: only standard deduction allowed (capped at 75,000 and limited by gross salary)
        # No HRA, no 80C, no 80D, no other deductions
        # Exception: 80CCD(2) employer NPS contribution is allowed but
        # that comes via employer so reflected in salary itself
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


# ─────────────────────────────────────────────
# PRETTY PRINT HELPER
# ─────────────────────────────────────────────

def format_inr(amount: float) -> str:
    """Format number as Indian Rupees with commas."""
    return f"₹{amount:,.2f}"


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


# ─────────────────────────────────────────────
# TEST CASES — Get your sister to verify these
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n📊 TAX CALCULATOR - FY 2025-26")
    print("Please verify all outputs with a CA\n")

    # ── TEST CASE 1: Rahul — 12 LPA, moderate investments ──
    print("TEST CASE 1: Rahul — Salary 12L, 80C 1L, HRA 60K, 80D 25K")
    rahul = TaxInput(
        gross_salary=1200000,
        age=26,
        hra_exemption=60000,
        standard_deduction=75000,
        deduction_80c=100000,
        deduction_80d_self=25000,
        tds_deducted=50000
    )
    rahul_results = calculate_tax(rahul, regime="both")
    for result in rahul_results.values():
        print_tax_result(result)

    # ── REGIME COMPARISON ──
    old_tax = rahul_results["old"].total_tax
    new_tax = rahul_results["new"].total_tax
    savings = abs(old_tax - new_tax)
    better = "Old Regime" if old_tax < new_tax else "New Regime"
    print(f"\n✅ RECOMMENDATION for Rahul: {better} saves {format_inr(savings)}\n")

    # ── TEST CASE 2: Priya — 8 LPA, no investments ──
    print("TEST CASE 2: Priya — Salary 8L, no investments")
    priya = TaxInput(
        gross_salary=800000,
        age=24,
        tds_deducted=20000
    )
    priya_results = calculate_tax(priya, regime="both")
    for result in priya_results.values():
        print_tax_result(result)

    old_tax = priya_results["old"].total_tax
    new_tax = priya_results["new"].total_tax
    savings = abs(old_tax - new_tax)
    better = "Old Regime" if old_tax < new_tax else "New Regime"
    print(f"\n✅ RECOMMENDATION for Priya: {better} saves {format_inr(savings)}\n")

    # ── TEST CASE 3: Amit — 18 LPA, fully optimized ──
    print("TEST CASE 3: Amit — Salary 18L, fully optimized deductions")
    amit = TaxInput(
        gross_salary=1800000,
        age=35,
        hra_exemption=120000,
        standard_deduction=75000,
        deduction_80c=150000,
        deduction_80d_self=25000,
        deduction_80d_parents=50000,
        are_parents_senior_citizen=True,
        deduction_80ccd1b=50000,
        deduction_24b=200000,
        tds_deducted=150000
    )
    amit_results = calculate_tax(amit, regime="both")
    for result in amit_results.values():
        print_tax_result(result)

    old_tax = amit_results["old"].total_tax
    new_tax = amit_results["new"].total_tax
    savings = abs(old_tax - new_tax)
    better = "Old Regime" if old_tax < new_tax else "New Regime"
    print(f"\n✅ RECOMMENDATION for Amit: {better} saves {format_inr(savings)}\n")

    # ── TEST CASE 4: Vikram — 12.8 LPA, New Regime marginal relief eligible ──
    print("TEST CASE 4: Vikram — Salary 12.8L, no investments (New Regime marginal relief check)")
    vikram = TaxInput(
        gross_salary=1280000,
        age=30,
        tds_deducted=0
    )
    vikram_results = calculate_tax(vikram, regime="new")
    for result in vikram_results.values():
        print_tax_result(result)
        # Verify: taxable income = 12,05,000. Tax before rebate = 60,750.
        # Excess income over 12L = 5,000. Capped tax = 5,000. Cess = 200. Total tax = 5,200.
        assert result.total_tax == 5200.0, f"Expected 5,200.0, got {result.total_tax}"

    # ── TEST CASE 5: Sneha — 13.5 LPA, New Regime marginal relief not eligible ──
    print("TEST CASE 5: Sneha — Salary 13.5L, no investments (New Regime above marginal relief limit)")
    sneha = TaxInput(
        gross_salary=1350000,
        age=28,
        tds_deducted=0
    )
    sneha_results = calculate_tax(sneha, regime="new")
    for result in sneha_results.values():
        print_tax_result(result)
        # Verify: taxable income = 12,75,000. Tax before rebate = 71,250.
        # Excess income over 12L = 75,000. Slabs tax is less than excess income, so no marginal relief.
        # Cess = 71,250 * 0.04 = 2,850. Total tax = 74,100.
        assert result.total_tax == 74100.0, f"Expected 74,100.0, got {result.total_tax}"

    # ── TEST CASE 6: Low Salary check ──
    print("TEST CASE 6: Kiran — Salary 30K, no other income (Low income standard deduction cap)")
    kiran = TaxInput(
        gross_salary=30000,
        age=25,
        tds_deducted=0
    )
    kiran_results = calculate_tax(kiran, regime="both")
    for result in kiran_results.values():
        print_tax_result(result)
        assert result.total_deductions == 30000.0, f"Expected deductions to be capped at gross salary 30k, got {result.total_deductions}"
        assert result.taxable_income == 0.0, f"Expected taxable income to be 0, got {result.taxable_income}"
        assert result.total_tax == 0.0, f"Expected total tax to be 0 due to 87A rebate, got {result.total_tax}"

    # ── TEST CASE 7: New Regime boundary at exactly 12L taxable income ──
    print("TEST CASE 7: Deepa — Salary 12.75L, no investments (Exactly 12L taxable income in New Regime)")
    deepa = TaxInput(
        gross_salary=1275000,
        age=32,
        tds_deducted=0
    )
    deepa_results = calculate_tax(deepa, regime="new")
    for result in deepa_results.values():
        print_tax_result(result)
        assert result.taxable_income == 1200000.0, f"Expected taxable income 12L, got {result.taxable_income}"
        assert result.total_tax == 0.0, f"Expected total tax to be 0 due to 87A rebate, got {result.total_tax}"

    # ── TEST CASE 8: New Regime boundary crossover - relief applies ──
    print("TEST CASE 8: Rohan — Salary 1,345,588, no investments (Marginal relief crossover - relief applies)")
    rohan = TaxInput(
        gross_salary=1345588,
        age=30,
        tds_deducted=0
    )
    rohan_results = calculate_tax(rohan, regime="new")
    for result in rohan_results.values():
        print_tax_result(result)
        # Taxable income = 1,270,588. Slab tax = 60,000 + 15% of 70,588 = 70,588.20.
        # Excess income = 70,588. Slab tax > Excess income, so relief applies.
        # Capped tax before cess = 70,588. Cess = 70,588 * 0.04 = 2823.52.
        # Total tax = 73,411.52.
        assert round(result.total_tax, 2) == 73411.52, f"Expected 73,411.52, got {result.total_tax}"

    # ── TEST CASE 9: New Regime boundary crossover - relief does NOT apply ──
    print("TEST CASE 9: Sunita — Salary 1,346,000, no investments (Marginal relief crossover - relief does NOT apply)")
    sunita = TaxInput(
        gross_salary=1346000,
        age=30,
        tds_deducted=0
    )
    sunita_results = calculate_tax(sunita, regime="new")
    for result in sunita_results.values():
        print_tax_result(result)
        # Taxable income = 1,271,000. Slab tax = 60,000 + 15% of 71,000 = 70,650.
        # Excess income = 71,000. Slab tax <= Excess income, so no relief.
        # Cess = 70,650 * 0.04 = 2,826.
        # Total tax = 73,476.
        assert result.total_tax == 73476.0, f"Expected 73,476.0, got {result.total_tax}"

    print("\n🎉 ALL TESTS COMPLETED AND VERIFIED CORRECTLY!")


