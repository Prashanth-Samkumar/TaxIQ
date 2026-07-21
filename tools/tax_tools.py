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
from langchain.tools import tool, ToolRuntime
import json 
from dataclasses import asdict

@tool
def create_profile_tool(profile: UserProfile,
                        notes: str = "",
                        *,
                        runtime: ToolRuntime[UserContext]) -> str:
    """Create a new profile and save to disk. Returns the user_id string."""
    
    return create_profile(runtime.context.user_id, profile, notes)

@tool
def update_profile_tool(updates: dict,
                        *,
                        runtime: ToolRuntime[UserContext]) -> str:
    """
    Update specific fields in the active profile.
    updates is a dict of field_name -> new_value.
    Only provided fields are updated, rest remain unchanged.
    Returns 'True' if success, or an error message otherwise.
    """
    
    res = update_profile(runtime.context.user_id, updates)
    return str(res)

@tool
def delete_profile_tool(*, runtime: ToolRuntime[UserContext]) -> str:
    """Delete the active profile permanently. Returns 'True' if success, or an error message."""
    
    res = delete_profile(runtime.context.user_id)
    return str(res)

@tool
def read_profile_tool(*, runtime: ToolRuntime[UserContext]) -> str:
    """Load the active profile details. Returns the StoredProfile details as a JSON string, or None."""
    
    res = read_profile(runtime.context.user_id)
    if res is None:
        return "None"
    return json.dumps(asdict(res), default=str)

@tool
def list_profiles_tool(*, runtime: ToolRuntime[UserContext]) -> str:
    """List all profiles belonging to the current user. Returns a list of summary dicts as a JSON string."""
    
    res = list_profiles(runtime.context.user_id)
    return json.dumps(res, default=str)

@tool
def get_profile_summary_tool(*, runtime: ToolRuntime[UserContext]) -> str:
    """Get a quick summary of the active profile. Returns a JSON string, or None."""
    
    res = get_profile_summary(runtime.context.user_id)
    return json.dumps(res, default=str)

@tool
def check_deductions_tool(*, runtime: ToolRuntime[UserContext]) -> str:
    """
    Analyze the active user profile to check deduction eligibility,
    utilized limits, remaining limits, and potential tax savings.
    Returns the deduction report as a JSON string, or 'None' if no profile exists.
    """
    profile_data = read_profile(runtime.context.user_id)
    if profile_data is None:
        return "None"
    report = check_deductions(profile_data.profile)
    return json.dumps(asdict(report), default=str)

@tool
def calculate_tax_tool(*, runtime: ToolRuntime[UserContext]) -> str:
    """
    Calculate the income tax liability under both Old and New regimes
    for the active user profile. Compare the results and break down by slab.
    Returns the tax calculation results as a JSON string, or 'None' if no profile exists.
    """
    profile_data = read_profile(runtime.context.user_id)
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
    