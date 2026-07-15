from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserContext:
    user_id: str


@dataclass
class UserProfile:
    """
    Complete profile of a salaried user.
    This is what the Profile Agent builds and maintains.
    All amounts in INR.
    """

    name: str
    age: int
    city: str
    is_metro: bool = False

    gross_salary: float = 0
    basic_salary: float = 0
    hra_received: float = 0
    rent_paid_monthly: float = 0

    epf_contribution: float = 0
    ppf_contribution: float = 0
    elss_investment: float = 0
    life_insurance_premium: float = 0
    home_loan_principal: float = 0
    nsc_investment: float = 0
    tuition_fees: float = 0
    sukanya_samriddhi: float = 0
    tax_saving_fd: float = 0

    self_health_insurance: float = 0
    parent_health_insurance: float = 0
    are_parents_senior_citizen: bool = False

    nps_contribution: float = 0

    education_loan_interest: float = 0

    donations_50_percent: float = 0
    donations_100_percent: float = 0

    savings_account_interest: float = 0

    home_loan_interest: float = 0
    has_home_loan: bool = False

    tds_deducted: float = 0
    other_income: float = 0

@dataclass
class ProfileMetadata:
    """Metadata stored alongside each profile."""
    user_id: str
    created_at: str
    last_updated: str
    financial_year: str
    notes: str = ""


@dataclass
class StoredProfile:
    """Complete stored profile with metadata and financial data."""
    profile: UserProfile
    metadata: ProfileMetadata


@dataclass
class DeductionItem:
    """Represents a single deduction with its status."""
    section: str
    name: str
    max_limit: float
    utilized: float
    remaining: float
    is_eligible: bool
    message: str
    is_missed: bool = False

@dataclass
class DeductionReport:
    """Complete deduction report for a user profile."""
    user_name: str
    total_possible_deductions: float
    total_utilized_deductions: float
    total_remaining_deductions: float
    potential_tax_saving: float
    items: list = field(default_factory=list)
    missed_opportunities: list = field(default_factory=list)
    alerts: list = field(default_factory=list)


@dataclass
class TaxInput:
    """
    Input to the tax calculator.
    All amounts in Indian Rupees (INR).
    """
    gross_salary: float
    age: int = 0
    hra_exemption: float = 0
    standard_deduction: float = 75000
    deduction_80c: float = 0
    deduction_80d_self: float = 0
    deduction_80d_parents: float = 0
    are_parents_senior_citizen: bool = False
    deduction_80ccd1b: float = 0
    deduction_80e: float = 0
    deduction_80g: float = 0
    deduction_80tta: float = 0
    deduction_80ttb: float = 0
    deduction_24b: float = 0
    other_income: float = 0
    tds_deducted: float = 0

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
    tax_payable_or_refund: float
    effective_tax_rate: float
    slab_breakdown: list


@dataclass
class ITR2Input:
    """
    Input to the ITR-2 tax calculator.
    All amounts in Indian Rupees (INR).
    """
    gross_salary: float
    age: int = 0
    hra_exemption: float = 0
    deduction_80c: float = 0
    deduction_80d_self: float = 0
    deduction_80d_parents: float = 0
    are_parents_senior_citizen: bool = False
    deduction_80ccd1b: float = 0
    deduction_80e: float = 0
    deduction_80g: float = 0
    deduction_80tta: float = 0
    deduction_80ttb: float = 0
    deduction_24b: float = 0
    other_income: float = 0
    dividend_income: float = 0
    
    cg_stcg_equity: float = 0
    cg_ltcg_equity: float = 0
    cg_ltcg_other: float = 0
    cg_stcg_other: float = 0
    
    tds_deducted: float = 0

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
