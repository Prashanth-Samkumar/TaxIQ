"""
Profile Reader and Writer Tool - FY 2025-26
Data layer for storing and retrieving user profiles.

This is what the Profile Agent uses to:
- Save new profiles
- Update profiles when user mentions financial info in chat
- Load profiles so the Conversation Agent can answer questions

Storage is JSON based for simplicity.
In production this would be a PostgreSQL database.

Author: Tax Intelligence System
Verified by: CA [Your Sister's Name]
"""

import json
import os
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from deduction_checker import UserProfile


# ─────────────────────────────────────────────
# STORAGE PATH
# ─────────────────────────────────────────────

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class ProfileMetadata:
    """Metadata stored alongside each profile."""
    profile_id: str
    owner_user_id: str        # Who created this profile (could manage multiple)
    relationship: str         # "self", "spouse", "parent", "child", "client"
    created_at: str
    last_updated: str
    financial_year: str       # "2025-26"
    notes: str = ""           # Any extra notes about this profile


@dataclass
class StoredProfile:
    """Complete stored profile with metadata and financial data."""
    metadata: ProfileMetadata
    profile: UserProfile


# ─────────────────────────────────────────────
# WRITE OPERATIONS
# ─────────────────────────────────────────────

def create_profile(owner_user_id: str,
                   profile: UserProfile,
                   relationship: str = "self",
                   notes: str = "") -> str:
    """
    Create a new profile and save to disk.
    Returns the profile_id.
    """
    profile_id = str(uuid.uuid4())[:8]  # Short ID for readability

    metadata = ProfileMetadata(
        profile_id=profile_id,
        owner_user_id=owner_user_id,
        relationship=relationship,
        created_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        financial_year="2025-26",
        notes=notes
    )

    stored = {
        "metadata": asdict(metadata),
        "profile": asdict(profile)
    }

    file_path = _get_profile_path(profile_id)
    with open(file_path, "w") as f:
        json.dump(stored, f, indent=2)

    print(f"  ✅ Profile created: {profile.name} (ID: {profile_id})")
    return profile_id


def update_profile(profile_id: str, updates: dict) -> bool:
    """
    Update specific fields in an existing profile.

    updates is a dict of field_name -> new_value.
    Only provided fields are updated, rest remain unchanged.

    This is what the Profile Agent calls after extracting
    financial information from a conversation.

    Example:
        update_profile("abc12345", {
            "rent_paid_monthly": 20000,
            "nps_contribution": 50000
        })
    """
    stored_data = _load_raw(profile_id)
    if not stored_data:
        print(f"  ❌ Profile not found: {profile_id}")
        return False

    # Apply updates to profile fields
    for field, value in updates.items():
        if field in stored_data["profile"]:
            old_value = stored_data["profile"][field]
            stored_data["profile"][field] = value
            print(f"  📝 Updated {field}: {old_value} → {value}")
        else:
            print(f"  ⚠️  Unknown field ignored: {field}")

    # Update timestamp
    stored_data["metadata"]["last_updated"] = datetime.now().isoformat()

    # Save back
    file_path = _get_profile_path(profile_id)
    with open(file_path, "w") as f:
        json.dump(stored_data, f, indent=2)

    print(f"  ✅ Profile {profile_id} updated successfully")
    return True


def delete_profile(profile_id: str) -> bool:
    """Delete a profile permanently."""
    file_path = _get_profile_path(profile_id)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"  ✅ Profile {profile_id} deleted")
        return True
    print(f"  ❌ Profile not found: {profile_id}")
    return False


# ─────────────────────────────────────────────
# READ OPERATIONS
# ─────────────────────────────────────────────

def read_profile(profile_id: str) -> Optional[StoredProfile]:
    """
    Load a profile by ID.
    Returns StoredProfile or None if not found.
    """
    stored_data = _load_raw(profile_id)
    if not stored_data:
        return None

    metadata = ProfileMetadata(**stored_data["metadata"])
    profile = UserProfile(**stored_data["profile"])

    return StoredProfile(metadata=metadata, profile=profile)


def list_profiles(owner_user_id: str) -> list[dict]:
    """
    List all profiles belonging to an owner.
    Returns a list of summary dicts (not full profiles).
    """
    profiles = []

    for filename in os.listdir(PROFILES_DIR):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(PROFILES_DIR, filename)
        with open(file_path, "r") as f:
            stored_data = json.load(f)

        if stored_data["metadata"]["owner_user_id"] == owner_user_id:
            profiles.append({
                "profile_id": stored_data["metadata"]["profile_id"],
                "name": stored_data["profile"]["name"],
                "relationship": stored_data["metadata"]["relationship"],
                "last_updated": stored_data["metadata"]["last_updated"],
                "gross_salary": stored_data["profile"]["gross_salary"],
                "notes": stored_data["metadata"]["notes"]
            })

    return profiles


def get_profile_summary(profile_id: str) -> Optional[dict]:
    """
    Get a quick summary of a profile without loading everything.
    Used by agents to quickly check what they know about a person.
    """
    stored_data = _load_raw(profile_id)
    if not stored_data:
        return None

    p = stored_data["profile"]
    m = stored_data["metadata"]

    # Calculate what is missing to help the Profile Agent
    missing_fields = []
    if p["basic_salary"] == 0:
        missing_fields.append("basic_salary")
    if p["hra_received"] == 0:
        missing_fields.append("hra_received")
    if p["epf_contribution"] == 0:
        missing_fields.append("epf_contribution")

    return {
        "profile_id": m["profile_id"],
        "name": p["name"],
        "relationship": m["relationship"],
        "gross_salary": p["gross_salary"],
        "has_home_loan": p["has_home_loan"],
        "pays_rent": p["rent_paid_monthly"] > 0,
        "has_nps": p["nps_contribution"] > 0,
        "has_health_insurance": p["self_health_insurance"] > 0,
        "has_parent_insurance": p["parent_health_insurance"] > 0,
        "last_updated": m["last_updated"],
        "missing_fields": missing_fields
    }


# ─────────────────────────────────────────────
# PROFILE AGENT HELPER
# ─────────────────────────────────────────────

def extract_and_update_from_conversation(profile_id: str,
                                          conversation_text: str,
                                          extracted_data: dict) -> bool:
    """
    This is the function the Profile Agent calls.

    The Profile Agent listens to conversation, extracts financial
    information using LLM, and passes it here as a structured dict.

    The LLM extraction prompt would say something like:
    "Extract any financial information mentioned in this conversation
    and return as JSON with field names matching UserProfile fields."

    Example extracted_data from LLM:
    {
        "rent_paid_monthly": 20000,
        "nps_contribution": 50000,
        "self_health_insurance": 15000
    }
    """
    if not extracted_data:
        return False

    print(f"\n  🤖 Profile Agent updating profile {profile_id}...")
    print(f"  📢 Extracted from conversation: {extracted_data}")
    return update_profile(profile_id, extracted_data)


# ─────────────────────────────────────────────
# PRIVATE HELPERS
# ─────────────────────────────────────────────

def _get_profile_path(profile_id: str) -> str:
    return os.path.join(PROFILES_DIR, f"{profile_id}.json")


def _load_raw(profile_id: str) -> Optional[dict]:
    file_path = _get_profile_path(profile_id)
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# PRETTY PRINT HELPERS
# ─────────────────────────────────────────────

def print_profile_list(profiles: list[dict], owner_id: str):
    print(f"\n{'='*55}")
    print(f"  PROFILES FOR USER: {owner_id}")
    print(f"{'='*55}")
    if not profiles:
        print("  No profiles found.")
    for p in profiles:
        print(f"\n  👤 {p['name']} ({p['relationship']})")
        print(f"     Profile ID  : {p['profile_id']}")
        print(f"     Salary      : ₹{p['gross_salary']:,.0f}")
        print(f"     Last Updated: {p['last_updated'][:10]}")
        if p['notes']:
            print(f"     Notes       : {p['notes']}")
    print(f"{'='*55}\n")


def print_profile_summary(summary: dict):
    print(f"\n{'='*55}")
    print(f"  PROFILE SUMMARY: {summary['name']}")
    print(f"{'='*55}")
    print(f"  Profile ID       : {summary['profile_id']}")
    print(f"  Relationship     : {summary['relationship']}")
    print(f"  Gross Salary     : ₹{summary['gross_salary']:,.0f}")
    print(f"  Pays Rent        : {'Yes' if summary['pays_rent'] else 'No'}")
    print(f"  Has Home Loan    : {'Yes' if summary['has_home_loan'] else 'No'}")
    print(f"  Has NPS          : {'Yes' if summary['has_nps'] else 'No'}")
    print(f"  Health Insurance : {'Yes' if summary['has_health_insurance'] else 'No'}")
    print(f"  Parent Insurance : {'Yes' if summary['has_parent_insurance'] else 'No'}")
    if summary['missing_fields']:
        print(f"  Missing Fields   : {', '.join(summary['missing_fields'])}")
    print(f"  Last Updated     : {summary['last_updated'][:10]}")
    print(f"{'='*55}\n")


# ─────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n💾 PROFILE READER AND WRITER - FY 2025-26\n")

    # ── TEST 1: Create profiles for a user ──
    print("TEST 1: Creating profiles for user 'user_001'")

    rahul_profile = UserProfile(
        name="Rahul",
        age=26,
        city="Chennai",
        is_metro=True,
        gross_salary=1200000,
        basic_salary=480000,
        hra_received=240000,
        rent_paid_monthly=15000,
        epf_contribution=57600,
        ppf_contribution=50000,
        savings_account_interest=5000,
        tds_deducted=50000
    )

    father_profile = UserProfile(
        name="Rajan (Father)",
        age=58,
        city="Chennai",
        is_metro=True,
        gross_salary=600000,
        basic_salary=240000,
        epf_contribution=28800,
        tds_deducted=10000
    )

    rahul_id = create_profile(
        owner_user_id="user_001",
        profile=rahul_profile,
        relationship="self",
        notes="Primary filer"
    )

    father_id = create_profile(
        owner_user_id="user_001",
        profile=father_profile,
        relationship="parent",
        notes="Retiring next year"
    )

    # ── TEST 2: List all profiles for user ──
    print("\nTEST 2: Listing all profiles for user_001")
    profiles = list_profiles("user_001")
    print_profile_list(profiles, "user_001")

    # ── TEST 3: Read a specific profile ──
    print("TEST 3: Reading Rahul's profile")
    stored = read_profile(rahul_id)
    if stored:
        print(f"  Loaded: {stored.profile.name}, Salary: ₹{stored.profile.gross_salary:,.0f}")
        print(f"  Created: {stored.metadata.created_at[:10]}")
        print(f"  Relationship: {stored.metadata.relationship}")

    # ── TEST 4: Profile Agent updates profile from conversation ──
    print("\nTEST 4: Profile Agent extracts and updates from conversation")
    conversation = "I just bought an NPS for 50000 and also started paying 25000 rent"
    extracted = {
        "nps_contribution": 50000,
        "rent_paid_monthly": 25000
    }
    extract_and_update_from_conversation(rahul_id, conversation, extracted)

    # ── TEST 5: Get profile summary ──
    print("\nTEST 5: Getting profile summary after update")
    summary = get_profile_summary(rahul_id)
    if summary:
        print_profile_summary(summary)

    # ── TEST 6: Verify update persisted by reading again ──
    print("TEST 6: Reading profile again to verify update persisted")
    stored_updated = read_profile(rahul_id)
    if stored_updated:
        print(f"  NPS after update: ₹{stored_updated.profile.nps_contribution:,.0f}")
        print(f"  Rent after update: ₹{stored_updated.profile.rent_paid_monthly:,.0f}/month")

    # ── CLEANUP: Delete test profiles ──
    print("\nCLEANUP: Deleting test profiles")
    delete_profile(rahul_id)
    delete_profile(father_id)
