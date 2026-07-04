from dataclasses import dataclass, field
from typing import Optional


# Runtime context schemas
@dataclass
class UserContext:
    user_id: str


# User profile schemas
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
class ProfileMetadata:
    """Metadata stored alongside each profile."""
    user_id: str
    created_at: str
    last_updated: str
    financial_year: str       # "2025-26"
    notes: str = ""           # Any extra notes about this profile


@dataclass
class StoredProfile:
    """Complete stored profile with metadata and financial data."""
    profile: UserProfile
    metadata: ProfileMetadata


# Detection schemas
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


# ITR1 schemas
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


# ITR2 schemas
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
