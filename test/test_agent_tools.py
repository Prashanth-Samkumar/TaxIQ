import unittest
import tempfile
import shutil
import os
import json
from unittest.mock import patch

from tools.schemas import UserProfile, UserContext
from tools.profile_store import create_profile
from agents.agent import check_deductions_tool, calculate_tax_tool

class DummyRuntime:
    def __init__(self, user_id):
        self.context = UserContext(user_id=user_id)

class TestAgentTools(unittest.TestCase):
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

    def test_tools_no_profile(self):
        runtime = DummyRuntime("user_no_profile")
        
        # Test check_deductions_tool
        deduction_res = check_deductions_tool.func(runtime=runtime)
        self.assertEqual(deduction_res, "None")
        
        # Test calculate_tax_tool
        tax_res = calculate_tax_tool.func(runtime=runtime)
        self.assertEqual(tax_res, "None")

    def test_tools_with_active_profile(self):
        profile = UserProfile(
            name="Rohan",
            age=30,
            city="Delhi",
            is_metro=True,
            gross_salary=1200000,
            basic_salary=480000,
            hra_received=240000,
            rent_paid_monthly=15000,
            epf_contribution=50000,
            ppf_contribution=30000
        )
        
        user_id = "user_rohan"
        create_profile(user_id=user_id, profile=profile, notes="Test integration")
        runtime = DummyRuntime(user_id)
        
        # Test check_deductions_tool
        deduction_res_str = check_deductions_tool.func(runtime=runtime)
        self.assertNotEqual(deduction_res_str, "None")
        deduction_res = json.loads(deduction_res_str)
        
        self.assertEqual(deduction_res["user_name"], "Rohan")
        # standard deduction 50k + HRA 132k + 80C 80k = 262k
        self.assertEqual(deduction_res["total_utilized_deductions"], 262000.0)
        
        # Test calculate_tax_tool
        tax_res_str = calculate_tax_tool.func(runtime=runtime)
        self.assertNotEqual(tax_res_str, "None")
        tax_res = json.loads(tax_res_str)
        
        self.assertIn("old", tax_res)
        self.assertIn("new", tax_res)
        
        # Verify Old regime tax calculation
        # Gross = 12L, deductions = 262k, taxable = 938k. Slab tax old = 12500 + 0.2 * 438000 = 100100. Cess = 4004. Total = 104104.0
        self.assertEqual(tax_res["old"]["taxable_income"], 938000.0)
        self.assertEqual(tax_res["old"]["total_tax"], 104104.0)
        
        # Verify New regime tax calculation
        # Gross = 12L, standard deduction = 75k, taxable = 1125k (<= 12L so total tax = 0 due to 87A)
        self.assertEqual(tax_res["new"]["taxable_income"], 1125000.0)
        self.assertEqual(tax_res["new"]["total_tax"], 0.0)

if __name__ == "__main__":
    unittest.main()
