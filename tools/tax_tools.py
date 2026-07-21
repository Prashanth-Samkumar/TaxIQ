import logging
import json 
from dataclasses import asdict
from langchain.tools import tool, ToolRuntime
from tools.schemas import UserContext, UserProfile, TaxInput
from tools.profile_store import (
    create_profile,
    update_profile,
    delete_profile,
    read_profile,
    list_profiles,
    get_profile_summary,
)
from rag import get_rag_pipeline
from tools.deduction_checker import check_deductions, calculate_hra_exemption
from tools.itr1_calculator import calculate_tax

logger = logging.getLogger(__name__)

@tool
def create_profile_tool(profile: UserProfile,
                        notes: str = "",
                        *,
                        runtime: ToolRuntime[UserContext]) -> str:
    """
    Create a new tax profile for a person or relative (e.g., Self, Mom, Dad, Spouse) and save to disk.
    Returns the created profile_id string.
    """
    return create_profile(runtime.context.user_id, profile, notes)

@tool
def update_profile_tool(updates: dict,
                        profile_name: str = "",
                        *,
                        runtime: ToolRuntime[UserContext]) -> str:
    """
    Update specific fields in a profile.
    updates is a dict of field_name -> new_value.
    profile_name (optional): target relative/person name (e.g. 'Mom', 'Dad', 'Prashanth').
    Returns 'True' if success, or an error message otherwise.
    """
    res = update_profile(runtime.context.user_id, updates, profile_name=profile_name)
    return str(res)

@tool
def delete_profile_tool(profile_name: str = "",
                        *,
                        runtime: ToolRuntime[UserContext]) -> str:
    """Delete a profile permanently by person/relative name. Returns 'True' if success, or an error message."""
    res = delete_profile(runtime.context.user_id, profile_name=profile_name)
    return str(res)

@tool
def read_profile_tool(profile_name: str = "",
                      *,
                      runtime: ToolRuntime[UserContext]) -> str:
    """Load profile details for a person/relative (e.g., 'Mom' or 'Self'). Returns StoredProfile JSON string, or None."""
    res = read_profile(runtime.context.user_id, profile_name=profile_name)
    if res is None:
        return "None"
    return json.dumps(asdict(res), default=str)

@tool
def list_profiles_tool(*, runtime: ToolRuntime[UserContext]) -> str:
    """List all tax profiles created for the current user and their family members/relatives. Returns JSON string list."""
    res = list_profiles(runtime.context.user_id)
    return json.dumps(res, default=str)

@tool
def get_profile_summary_tool(profile_name: str = "",
                            *,
                            runtime: ToolRuntime[UserContext]) -> str:
    """Get a quick summary of a profile by person/relative name. Returns a JSON string, or None."""
    res = get_profile_summary(runtime.context.user_id, profile_name=profile_name)
    return json.dumps(res, default=str)

@tool
def check_deductions_tool(profile_name: str = "",
                          *,
                          runtime: ToolRuntime[UserContext]) -> str:
    """
    Analyze tax profile for a person/relative name to check deduction eligibility,
    utilized limits, remaining limits, and potential tax savings.
    Returns the deduction report as a JSON string, or 'None' if no profile exists.
    """
    profile_data = read_profile(runtime.context.user_id, profile_name=profile_name)
    if profile_data is None:
        return "None"
    report = check_deductions(profile_data.profile)
    return json.dumps(asdict(report), default=str)

@tool
def calculate_tax_tool(profile_name: str = "",
                       *,
                       runtime: ToolRuntime[UserContext]) -> str:
    """
    Calculate income tax liability under both Old and New regimes for a person/relative name.
    Compare results and break down by slab.
    Returns tax calculation results as a JSON string, or 'None' if no profile exists.
    """
    profile_data = read_profile(runtime.context.user_id, profile_name=profile_name)
    if profile_data is None:
        return "None"
    
    profile = profile_data.profile
    hra_exemp = calculate_hra_exemption(profile)
    
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
    
    total_donations = profile.donations_100_percent + (profile.donations_50_percent * 0.5)
    
    tax_input = TaxInput(
        gross_salary=profile.gross_salary,
        age=profile.age,
        hra_exemption=hra_exemp,
        deduction_80c=total_80c,
        deduction_80d_self=profile.self_health_insurance,
        deduction_80d_parents=profile.parent_health_insurance,
        are_parents_senior_citizen=profile.are_parents_senior_citizen,
        deduction_80ccd1b=profile.nps_contribution,
        deduction_80e=profile.education_loan_interest,
        deduction_80g=total_donations,
        deduction_80tta=profile.savings_account_interest,
        deduction_80ttb=profile.savings_account_interest + profile.other_income,
        deduction_24b=profile.home_loan_interest if profile.has_home_loan else 0,
        other_income=profile.other_income,
        tds_deducted=profile.tds_deducted
    )
    
    results = calculate_tax(tax_input, regime="both")
    serialized_results = {regime: asdict(res) for regime, res in results.items()}
    return json.dumps(serialized_results, default=str)

@tool
def rag_query_tool(query: str, *, runtime: ToolRuntime[UserContext]) -> str:
    """
    Query the RAG index for relevant information.
    Returns the retrieved chunks as a JSON string.
    """
    rag_pipeline = get_rag_pipeline()
    try:
        results = rag_pipeline.retrieve(query, k=3)
    except Exception:
        logger.exception("RAG retrieval failed for query=%r", query)
        return json.dumps({"error": "retrieval_failed"})
    return json.dumps(results, default=str)