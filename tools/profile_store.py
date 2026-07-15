"""
Profile Reader and Writer Tool - FY 2025-26
Data layer for storing and retrieving user profiles.

This is what the Profile Agent uses to:
- Save new profiles
- Update profiles when user mentions financial info in chat
- Load profiles so the Conversation Agent can answer questions

Storage is JSON based for simplicity.
In production this would be a PostgreSQL database.

"""

import json
import os
from datetime import datetime
from dataclasses import asdict
from typing import Optional

from .schemas import ProfileMetadata, StoredProfile, UserProfile

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

def create_profile(user_id: str,
                   profile: UserProfile,
                   notes: str = "") -> str:
    """
    Create a new profile and save to disk.
    Returns the user_id.
    """
    metadata = ProfileMetadata(
        user_id=user_id,
        created_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        financial_year="2025-26",
        notes=notes
    )

    stored = {
        "metadata": asdict(metadata),
        "profile": asdict(profile)
    }

    file_path = _get_profile_path(user_id)
    with open(file_path, "w") as f:
        json.dump(stored, f, indent=2)

    print(f"  [OK] Profile created: {profile.name} (User ID: {user_id})")
    return user_id

def update_profile(user_id: str, updates: dict) -> bool:
    """
    Update specific fields in an existing profile.

    updates is a dict of field_name -> new_value.
    Only provided fields are updated, rest remain unchanged.
    """
    stored_data = _load_raw(user_id)
    if not stored_data:
        print(f"  [ERROR] Profile not found: {user_id}")
        return False

    for field, value in updates.items():
        if field in stored_data["profile"]:
            old_value = stored_data["profile"][field]
            stored_data["profile"][field] = value
            print(f"  [UPDATE] Updated {field}: {old_value} -> {value}")
        else:
            print(f"  [WARNING] Unknown field ignored: {field}")

    stored_data["metadata"]["last_updated"] = datetime.now().isoformat()

    file_path = _get_profile_path(user_id)
    with open(file_path, "w") as f:
        json.dump(stored_data, f, indent=2)

    print(f"  [OK] Profile for {user_id} updated successfully")
    return True

def delete_profile(user_id: str) -> bool:
    """Delete a profile permanently."""
    file_path = _get_profile_path(user_id)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"  [OK] Profile for {user_id} deleted")
        return True
    print(f"  [ERROR] Profile not found: {user_id}")
    return False



def read_profile(user_id: str) -> Optional[StoredProfile]:
    """
    Load a profile by user_id.
    Returns StoredProfile or None if not found.
    """
    stored_data = _load_raw(user_id)
    if not stored_data:
        return None

    metadata = ProfileMetadata(**stored_data["metadata"])
    profile = UserProfile(**stored_data["profile"])

    return StoredProfile(metadata=metadata, profile=profile)

def list_profiles(user_id: str) -> list[dict]:
    """
    List the profile belonging to the user.
    Returns a list containing a summary dict if it exists, otherwise empty.
    """
    file_path = _get_profile_path(user_id)
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r") as f:
        stored_data = json.load(f)

    m = stored_data["metadata"]
    p = stored_data["profile"]
    return [{
        "user_id": m["user_id"],
        "name": p["name"],
        "last_updated": m["last_updated"],
        "gross_salary": p["gross_salary"],
        "notes": m["notes"]
    }]

def get_profile_summary(user_id: str) -> Optional[dict]:
    """
    Get a quick summary of a profile without loading everything.
    Used by agents to quickly check what they know about a person.
    """
    stored_data = _load_raw(user_id)
    if not stored_data:
        return None

    p = stored_data["profile"]
    m = stored_data["metadata"]

    missing_fields = []
    if p["basic_salary"] == 0:
        missing_fields.append("basic_salary")
    if p["hra_received"] == 0:
        missing_fields.append("hra_received")
    if p["epf_contribution"] == 0:
        missing_fields.append("epf_contribution")

    return {
        "user_id": m["user_id"],
        "name": p["name"],
        "gross_salary": p["gross_salary"],
        "has_home_loan": p["has_home_loan"],
        "pays_rent": p["rent_paid_monthly"] > 0,
        "has_nps": p["nps_contribution"] > 0,
        "has_health_insurance": p["self_health_insurance"] > 0,
        "has_parent_insurance": p["parent_health_insurance"] > 0,
        "last_updated": m["last_updated"],
        "missing_fields": missing_fields
    }



def extract_and_update_from_conversation(user_id: str,
                                          conversation_text: str,
                                          extracted_data: dict) -> bool:
    """
    This is the function the Profile Agent calls.

    The Profile Agent listens to conversation, extracts financial
    information using LLM, and passes it here as a structured dict.
    """
    if not extracted_data:
        return False

    print(f"\n  [AGENT] Profile Agent updating profile for {user_id}...")
    print(f"  [INFO] Extracted from conversation: {extracted_data}")
    return update_profile(user_id, extracted_data)



def _get_profile_path(user_id: str) -> str:
    return os.path.join(PROFILES_DIR, f"{user_id}.json")


def _load_raw(user_id: str) -> Optional[dict]:
    file_path = _get_profile_path(user_id)
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as f:
        return json.load(f)



def print_profile_list(profiles: list[dict], user_id: str):
    print(f"\n{'='*55}")
    print(f"  PROFILES FOR USER: {user_id}")
    print(f"{'='*55}")
    if not profiles:
        print("  No profiles found.")
    for p in profiles:
        print(f"\n  [USER] {p['name']}")
        print(f"     User ID     : {p['user_id']}")
        print(f"     Salary      : Rs. {p['gross_salary']:,.0f}")
        print(f"     Last Updated: {p['last_updated'][:10]}")
        if p['notes']:
            print(f"     Notes       : {p['notes']}")
    print(f"{'='*55}\n")


def print_profile_summary(summary: dict):
    print(f"\n{'='*55}")
    print(f"  PROFILE SUMMARY: {summary['name']}")
    print(f"{'='*55}")
    print(f"  User ID          : {summary['user_id']}")
    print(f"  Gross Salary     : Rs. {summary['gross_salary']:,.0f}")
    print(f"  Pays Rent        : {'Yes' if summary['pays_rent'] else 'No'}")
    print(f"  Has Home Loan    : {'Yes' if summary['has_home_loan'] else 'No'}")
    print(f"  Has NPS          : {'Yes' if summary['has_nps'] else 'No'}")
    print(f"  Health Insurance : {'Yes' if summary['has_health_insurance'] else 'No'}")
    print(f"  Parent Insurance : {'Yes' if summary['has_parent_insurance'] else 'No'}")
    if summary['missing_fields']:
        print(f"  Missing Fields   : {', '.join(summary['missing_fields'])}")
    print(f"  Last Updated     : {summary['last_updated'][:10]}")
    print(f"{'='*55}\n")
