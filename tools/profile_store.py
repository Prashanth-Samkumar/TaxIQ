"""
Profile Reader and Writer Tool - FY 2025-26
Data layer for storing and retrieving user tax profiles.

Supports storing and managing multiple tax profiles for a personal single-user app
(e.g. Self, Mom, Dad, Spouse, Sibling).
"""

import json
import os
import re
from datetime import datetime
from dataclasses import asdict
from typing import Optional

from .schemas import ProfileMetadata, StoredProfile, UserProfile

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

def _slugify(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_').lower()

def _get_profile_file(user_id: str, profile_name: str = "") -> tuple[str, str]:
    """
    Returns (profile_id, file_path).
    If profile_name is given, constructs unique key `user_id_slugifiedname`.
    If profile_name is empty, uses `user_id`.
    """
    if profile_name:
        slug = _slugify(profile_name)
        profile_id = f"{user_id}_{slug}" if slug else user_id
        return profile_id, os.path.join(PROFILES_DIR, f"{profile_id}.json")
    return user_id, os.path.join(PROFILES_DIR, f"{user_id}.json")

def create_profile(user_id: str,
                   profile: UserProfile,
                   notes: str = "") -> str:
    """
    Create a new profile and save to disk.
    Returns the profile_id or user_id.
    """
    profile_id, file_path = _get_profile_file(user_id, profile.name)

    metadata = ProfileMetadata(
        user_id=user_id,
        created_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        financial_year="2025-26",
        notes=notes or f"Profile for {profile.name}"
    )

    stored = {
        "metadata": asdict(metadata),
        "profile": asdict(profile)
    }

    with open(file_path, "w") as f:
        json.dump(stored, f, indent=2)

    print(f"  [OK] Profile created: {profile.name} (File ID: {profile_id})")
    return profile_id

def _find_profile_file(user_id: str, profile_name: str = "") -> Optional[str]:
    """
    Find matching profile JSON file path for user_id and optional profile_name.
    """
    if not os.path.exists(PROFILES_DIR):
        return None

    all_files = [f for f in os.listdir(PROFILES_DIR) if f.endswith(".json")]
    if not all_files:
        return None

    candidates = []
    for fname in all_files:
        fpath = os.path.join(PROFILES_DIR, fname)
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
                m = data.get("metadata", {})
                p = data.get("profile", {})
                if m.get("user_id") == user_id or fname.startswith(f"{user_id}_") or fname == f"{user_id}.json":
                    candidates.append((fpath, fname, m, p))
        except Exception:
            continue

    if not candidates:
        # Fallback to any valid profile if single-user app
        for fname in all_files:
            fpath = os.path.join(PROFILES_DIR, fname)
            try:
                with open(fpath, "r") as f:
                    data = json.load(f)
                    candidates.append((fpath, fname, data.get("metadata", {}), data.get("profile", {})))
            except Exception:
                continue

    if not candidates:
        return None

    if profile_name:
        target_norm = profile_name.lower().strip()
        for fpath, fname, m, p in candidates:
            p_name = p.get("name", "").lower()
            m_notes = m.get("notes", "").lower()
            if target_norm in p_name or target_norm in m_notes or target_norm in fname.lower():
                return fpath

    # Sort by last_updated (most recent)
    candidates.sort(key=lambda x: x[2].get("last_updated", ""), reverse=True)
    return candidates[0][0]

def update_profile(user_id: str, updates: dict, profile_name: str = "") -> bool:
    """
    Update specific fields in an existing profile.
    """
    file_path = _find_profile_file(user_id, profile_name)
    if not file_path or not os.path.exists(file_path):
        print(f"  [ERROR] Profile not found for {user_id} ({profile_name})")
        return False

    with open(file_path, "r") as f:
        stored_data = json.load(f)

    for field, value in updates.items():
        if field in stored_data["profile"]:
            old_value = stored_data["profile"][field]
            stored_data["profile"][field] = value
            print(f"  [UPDATE] Updated {field}: {old_value} -> {value}")
        else:
            print(f"  [WARNING] Unknown field ignored: {field}")

    stored_data["metadata"]["last_updated"] = datetime.now().isoformat()

    with open(file_path, "w") as f:
        json.dump(stored_data, f, indent=2)

    print(f"  [OK] Profile in {os.path.basename(file_path)} updated successfully")
    return True

def delete_profile(user_id: str, profile_name: str = "") -> bool:
    """Delete a profile permanently."""
    file_path = _find_profile_file(user_id, profile_name)
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        print(f"  [OK] Profile {file_path} deleted")
        return True
    print(f"  [ERROR] Profile not found to delete for {user_id} ({profile_name})")
    return False

def read_profile(user_id: str, profile_name: str = "") -> Optional[StoredProfile]:
    """
    Load a profile by user_id and optional profile_name.
    """
    file_path = _find_profile_file(user_id, profile_name)
    if not file_path or not os.path.exists(file_path):
        return None

    with open(file_path, "r") as f:
        stored_data = json.load(f)

    metadata = ProfileMetadata(**stored_data["metadata"])
    profile = UserProfile(**stored_data["profile"])

    return StoredProfile(metadata=metadata, profile=profile)

def list_profiles(user_id: str) -> list[dict]:
    """
    List all profiles belonging to the user.
    """
    if not os.path.exists(PROFILES_DIR):
        return []

    results = []
    seen_files = set()
    for fname in os.listdir(PROFILES_DIR):
        if not fname.endswith(".json") or fname in seen_files:
            continue
        seen_files.add(fname)
        fpath = os.path.join(PROFILES_DIR, fname)
        try:
            with open(fpath, "r") as f:
                stored_data = json.load(f)
                m = stored_data["metadata"]
                p = stored_data["profile"]
                results.append({
                    "user_id": m.get("user_id", user_id),
                    "name": p.get("name", "Unknown"),
                    "age": p.get("age", 0),
                    "city": p.get("city", ""),
                    "last_updated": m.get("last_updated", ""),
                    "gross_salary": p.get("gross_salary", 0),
                    "notes": m.get("notes", "")
                })
        except Exception:
            continue

    return results

def get_profile_summary(user_id: str, profile_name: str = "") -> Optional[dict]:
    """
    Get a quick summary of a profile.
    """
    file_path = _find_profile_file(user_id, profile_name)
    if not file_path or not os.path.exists(file_path):
        return None

    with open(file_path, "r") as f:
        stored_data = json.load(f)

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
        "age": p["age"],
        "city": p["city"],
        "gross_salary": p["gross_salary"],
        "has_home_loan": p["has_home_loan"],
        "pays_rent": p["rent_paid_monthly"] > 0,
        "has_nps": p["nps_contribution"] > 0,
        "has_health_insurance": p["self_health_insurance"] > 0,
        "has_parent_insurance": p["parent_health_insurance"] > 0,
        "last_updated": m["last_updated"],
        "notes": m.get("notes", ""),
        "missing_fields": missing_fields
    }

def print_profile_list(profiles: list[dict], user_id: str):
    print(f"\n{'='*55}")
    print(f"  PROFILES FOR USER: {user_id}")
    print(f"{'='*55}")
    if not profiles:
        print("  No profiles found.")
    for p in profiles:
        print(f"\n  [PROFILE] {p['name']}")
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
