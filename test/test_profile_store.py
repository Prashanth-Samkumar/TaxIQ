import unittest
import tempfile
import shutil
import os
from unittest.mock import patch

from tools.schemas import UserProfile
import tools.profile_store
from tools.profile_store import (
    create_profile,
    read_profile,
    update_profile,
    delete_profile,
    list_profiles,
    get_profile_summary,
    extract_and_update_from_conversation
)


class TestProfileStore(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for storing profiles during tests
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch("tools.profile_store.PROFILES_DIR", self.test_dir)
        self.patcher.start()

    def tearDown(self):
        # Clean up patch and temp folder
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_profile_lifecycle_and_crud(self):
        # ── Test 1: Profile creation ──
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

        user_id = "user_001"
        res_user_id = create_profile(
            user_id=user_id,
            profile=rahul_profile,
            notes="Primary filer"
        )

        self.assertEqual(res_user_id, user_id)

        # ── Test 2: List profiles ──
        profiles = list_profiles(user_id)
        self.assertEqual(len(profiles), 1)
        
        # Verify Rahul is in the list
        rahul_listed = profiles[0]
        self.assertEqual(rahul_listed["name"], "Rahul")
        self.assertEqual(rahul_listed["notes"], "Primary filer")

        # ── Test 3: Read profile ──
        stored = read_profile(user_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.profile.name, "Rahul")
        self.assertEqual(stored.metadata.user_id, user_id)
        
        # ── Test 4: Extract and update from conversation ──
        conversation = "I just bought an NPS for 50000 and also started paying 25000 rent"
        extracted = {
            "nps_contribution": 50000,
            "rent_paid_monthly": 25000
        }
        success = extract_and_update_from_conversation(user_id, conversation, extracted)
        self.assertTrue(success)

        # ── Test 5: Verify update persisted by reading again ──
        stored_updated = read_profile(user_id)
        self.assertIsNotNone(stored_updated)
        self.assertEqual(stored_updated.profile.nps_contribution, 50000)
        self.assertEqual(stored_updated.profile.rent_paid_monthly, 25000)

        # ── Test 6: Get summary ──
        summary = get_profile_summary(user_id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary["name"], "Rahul")
        self.assertTrue(summary["has_nps"])
        self.assertTrue(summary["pays_rent"])

        # ── Test 7: Delete profiles ──
        del_rahul = delete_profile(user_id)
        self.assertTrue(del_rahul)
        
        # Verify listing is empty
        profiles_after_delete = list_profiles(user_id)
        self.assertEqual(len(profiles_after_delete), 0)

        # Read deleted profile returns None
        self.assertIsNone(read_profile(user_id))

if __name__ == "__main__":
    unittest.main()
